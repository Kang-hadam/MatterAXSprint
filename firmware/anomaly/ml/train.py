"""Train, calibrate, evaluate and export the recognise-then-judge temperature anomaly model.

The device recognises its space in the first 5 minutes (level, noise) and learns the daily profile from
the first 24 hours on (ml/features.py); the network judges every later minute relative to that:
  context (8) -> Linear -> ReLU (H) -> Linear -> [mu (6), beta (6)]      beta = log2 of 1/sigma
  z = (y - mu) * 2^beta,  score = mean z^2,  anomaly if score >= threshold
y holds the window features relative to what was recognised. Trained from scratch (random init) on normal
streams of five simulated spaces only (Gaussian NLL, size picked by validation NLL). The threshold
maximises window accuracy on labelled dev streams - iterated, because alarms postpone the first learning
of the profile. Test streams (their own seed) are used only for the report.
"""
from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import numpy as np
import torch

import data as D
import features as F

ROOT = Path(__file__).resolve().parent.parent
f32 = np.float32
SPLITS = {"train": (40, False), "val": (10, False), "dev": (10, True), "test": (20, True)}  # streams per space
DAYS = 7


def load(split: str, seed: int, cache: Path) -> dict:
    """Window features + labels of one split (simulated once, cached as .npz)."""
    path = cache / f"{split}_{seed}.npz"
    if path.exists():
        return dict(np.load(path))
    t0 = time.time()
    n, labelled = SPLITS[split]
    r = D.simulate(n, DAYS, [seed, list(SPLITS).index(split)], labelled)
    out = dict(F.window_stats(r["temp"]), sec0=r["sec0"], env=r["env"], label=r["label"], wtype=r["wtype"])
    cache.mkdir(parents=True, exist_ok=True)
    np.savez(path, **out)
    print(f"  {split}: {len(r['sec0'])} streams x {DAYS} days simulated in {time.time() - t0:.0f}s")
    return out


class Candidates(torch.nn.Module):
    """K independent tiny MLPs (hidden size x seed) trained side by side in one batched GPU pass."""

    def __init__(self, cands: list[tuple[int, int]]):
        super().__init__()
        hmax, k = max(h for h, _ in cands), len(cands)
        w1, b1 = torch.empty(k, hmax, F.NCTX), torch.empty(k, hmax)
        w2, mask = torch.empty(k, 2 * F.NFEAT, hmax), torch.zeros(k, hmax)
        for i, (h, seed) in enumerate(cands):                     # random init: trained from scratch
            g = torch.Generator().manual_seed(seed)
            w1[i] = torch.randn(hmax, F.NCTX, generator=g) * math.sqrt(2 / F.NCTX)
            b1[i] = (torch.rand(hmax, generator=g) * 2 - 1) * 0.5
            w2[i] = torch.randn(2 * F.NFEAT, hmax, generator=g) * (0.1 / math.sqrt(h))
            mask[i, :h] = 1
        self.w1, self.b1, self.w2 = (torch.nn.Parameter(t) for t in (w1, b1, w2))
        self.b2 = torch.nn.Parameter(torch.zeros(k, 2 * F.NFEAT))
        self.mask = torch.nn.Parameter(mask, requires_grad=False)

    def forward(self, c):                                          # c [N, NCTX] -> mu, beta [K, N, NFEAT]
        h = torch.relu(torch.einsum("khi,ni->knh", self.w1, c) + self.b1[:, None]) * self.mask[:, None]
        return (torch.einsum("koh,knh->kno", self.w2, h) + self.b2[:, None]).chunk(2, dim=-1)

    def nll(self, c, y):                                           # Gaussian NLL per candidate [nats/feature]
        mu, beta = self(c)
        z = (y - mu) * torch.exp2(beta)
        return (0.5 * z * z - beta * math.log(2)).mean((1, 2))


def train(model: Candidates, tr, va, steps: int, lr: float, batch: int) -> np.ndarray:
    params = [p for p in model.parameters() if p.requires_grad]
    opt = torch.optim.Adam(params, lr=lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, steps, eta_min=lr * 0.01)
    dev = model.b2.device
    best = torch.full((model.b2.shape[0],), math.inf, device=dev)
    snap = {n: p.detach().clone() for n, p in model.named_parameters()}
    gen = torch.Generator(device=dev).manual_seed(0)
    for step in range(steps + 1):
        if step % 100 == 0 or step == steps:                       # early stopping per candidate (val NLL)
            with torch.no_grad():
                v = model.nll(*va)
            better = v < best
            best = torch.where(better, v, best)
            for n, p in model.named_parameters():
                snap[n][better] = p.detach()[better]
        if step == steps:
            break
        idx = torch.randint(0, len(tr[0]), (batch,), device=dev, generator=gen)
        loss = model.nll(tr[0][idx], tr[1][idx]).sum()
        opt.zero_grad(set_to_none=True)
        loss.backward()
        opt.step()
        sched.step()
    with torch.no_grad():
        for n, p in model.named_parameters():
            p.copy_(snap[n])
    return best.cpu().numpy()


def export_params(model: Candidates, i: int, h: int, norm: tuple) -> dict:
    """Candidate i -> float32 deploy weights with input and output normalisation folded in."""
    cmu, csd, ymu, ysd = norm
    w1 = model.w1[i, :h].detach().cpu().double().numpy() / csd
    b1 = model.b1[i, :h].detach().cpu().double().numpy() - w1 @ cmu
    w2 = model.w2[i, :, :h].detach().cpu().double().numpy()
    b2 = model.b2[i].detach().cpu().double().numpy()
    w2[:F.NFEAT] *= ysd[:, None]                                   # mu_raw = ymu + ysd * mu
    b2[:F.NFEAT] = b2[:F.NFEAT] * ysd + ymu
    b2[F.NFEAT:] -= np.log2(ysd)                                   # beta_raw = beta - log2(ysd)
    return {k: v.astype(f32) for k, v in dict(w1=w1, b1=b1, w2=w2, b2=b2).items()}


def best_threshold(score: np.ndarray, label: np.ndarray) -> float:
    """Threshold with maximum window accuracy (alarm if score >= threshold)."""
    o = np.argsort(-score, kind="stable")
    gain = np.cumsum(label[o].astype(np.int64)) - np.cumsum(~label[o])
    return float(score[o[int(np.argmax(gain))]])


def calibrate(P: dict, dv: dict, basic_grid: list[float], thr_full: float) -> tuple:
    """(BASIC, FULL) thresholds with the best dev window accuracy. BASIC alarms also keep first-day
    anomalies out of the learned profile, so every BASIC candidate is scored on the whole deployment
    with its FULL threshold re-fitted (iterated: alarms change what the device learns)."""
    seen = {}
    y = dv["label"].astype(bool)
    for tb in basic_grid:
        tf = thr_full
        for _ in range(4):
            r = F.run(dv, dv["sec0"], P, (tb, tf))
            m = r["phase"] > 0
            seen[(tb, tf)] = float((r["alarm"][m] == y[m]).mean())
            full = r["phase"] == 2
            new = float(f32(best_threshold(r["score"][full], y[full])))
            if (tb, new) in seen:
                break
            tf = new
        tb_best = max((k for k in seen if k[0] == tb), key=lambda k: seen[k])
        print(f"  BASIC {tb:7.3f}: best FULL {tb_best[1]:.3f} -> dev accuracy {seen[tb_best]:.4f}")
    return max(seen, key=lambda k: seen[k])


def runs(mask: np.ndarray) -> list[tuple[int, int]]:
    d = np.diff(np.r_[0, mask.astype(np.int8), 0])
    return list(zip(np.flatnonzero(d == 1).tolist(), np.flatnonzero(d == -1).tolist()))


def evaluate(ds: dict, r: dict) -> dict:
    """Window metrics over judged windows (after the recognition minutes) + per phase/space/day/type."""
    m, y, p = r["phase"] > 0, ds["label"].astype(bool), r["alarm"]

    def stats(mask):
        yy, pp = y[mask], p[mask]
        tp, fp = int((pp & yy).sum()), int((pp & ~yy).sum())
        tn, fn = int((~pp & ~yy).sum()), int((~pp & yy).sum())
        return dict(windows=int(mask.sum()), accuracy=round((tp + tn) / max(tp + fp + tn + fn, 1), 4),
                    recall=round(tp / max(tp + fn, 1), 4), precision=round(tp / max(tp + fp, 1), 4),
                    false_positive_rate=round(fp / max(fp + tn, 1), 4), tp=tp, fp=fp, tn=tn, fn=fn)

    res: dict = stats(m)
    res["balanced_accuracy"] = round(0.5 * (res["recall"] + 1 - res["false_positive_rate"]), 4)
    res["f1"] = round(2 * res["precision"] * res["recall"] / max(res["precision"] + res["recall"], 1e-9), 4)
    s, yy = r["score"][m], y[m]
    rank = np.empty(len(s))
    rank[np.argsort(s, kind="stable")] = np.arange(1, len(s) + 1)
    n1, n0 = int(yy.sum()), int((~yy).sum())
    res["roc_auc"] = round(float((rank[yy].sum() - n1 * (n1 + 1) / 2) / max(n1 * n0, 1)), 4)
    res["per_phase"] = {F.PHASES[ph]: stats(m & (r["phase"] == ph)) for ph in (1, 2)}
    env = np.broadcast_to(ds["env"][:, None], y.shape)
    res["per_space"] = {D.ENVS[e]: stats(m & (env == e)) for e in range(len(D.ENVS))}
    day = np.broadcast_to(np.arange(y.shape[1])[None] // F.DAY_WIN, y.shape)
    res["accuracy_per_day"] = {f"day{d + 1}": stats(m & (day == d))["accuracy"] for d in range(y.shape[1] // F.DAY_WIN)}
    res["recall_per_type"] = {t: round(float(p[m & (ds["wtype"] == i + 1)].mean()), 4)
                              for i, t in enumerate(D.TYPES) if (m & (ds["wtype"] == i + 1)).any()}
    ev = det = fa = 0
    for n in range(len(y)):
        lab, al = y[n] & m[n], p[n] & m[n]
        for a, b in runs(lab):
            ev += 1
            det += int(al[a:b].any())
        fa += sum(1 for a, b in runs(al) if not lab[a:b].any())
    res.update(events=ev, events_detected=det,
               false_alarm_runs_per_day=round(fa / (len(y) * y.shape[1] / F.DAY_WIN), 2))
    return res


def fnv1a(scores: np.ndarray) -> int:
    h = 2166136261
    for b in np.asarray(scores, f32).astype("<f4").tobytes():
        h = ((h ^ b) * 16777619) & 0xFFFFFFFF
    return h


def cf(v) -> str:
    s = "%.9g" % float(f32(v))
    return (s if any(c in s for c in ".en") else s + ".0") + "f"


def carr(a: np.ndarray) -> str:
    if a.ndim == 1:
        return "{" + ", ".join(cf(v) for v in a) + "}"
    return "{\n    " + ",\n    ".join(carr(r) for r in a) + "\n}"


def write_model_header(path: Path, P: dict, thr: tuple, meta: str):
    path.write_text(f"""/* Generated by ml/train.py - do not edit. {meta} */
#ifndef ANOMALY_MODEL_H_
#define ANOMALY_MODEL_H_

#if AD_WINDOW != {F.WINDOW} || AD_RECOG != {F.RECOG} || AD_SLOTS != {F.SLOTS} || AD_SLOT_SEC != {F.SLOT_SEC} || \\
	AD_NMAX != {F.NMAX} || AD_MINCNT != {F.MINCNT} || AD_DAY_WIN != {F.DAY_WIN}
#error "anomaly.h does not match the model generated by ml/train.py"
#endif

#define AD_NFEAT       {F.NFEAT}
#define AD_NCTX        {F.NCTX}
#define AD_HIDDEN      {len(P["b1"])}
#define AD_EMA_ALPHA   {cf(F.EMA_ALPHA)}
#define AD_EPS_VAR     {cf(F.EPS_VAR)}
#define AD_EPS_RNG     {cf(F.EPS_RNG)}
#define AD_EPS_SL      {cf(F.EPS_SL)}
#define AD_EPS_D       {cf(F.EPS_D)}
#define AD_DFLOOR      {cf(F.DFLOOR)}
#define AD_CLIP_K      {cf(F.CLIP_K)}
#define AD_THR_BASIC   {cf(thr[0])}
#define AD_THR_FULL    {cf(thr[1])}
#define AD_LOG2_C      {", ".join(cf(c) for c in F.LOG2_C)}
#define AD_EXP2_C      {", ".join(cf(c) for c in F.EXP2_C)}

static const float ad_w1[AD_HIDDEN][AD_NCTX] = {carr(P["w1"])};
static const float ad_b1[AD_HIDDEN] = {carr(P["b1"])};
static const float ad_w2[2 * AD_NFEAT][AD_HIDDEN] = {carr(P["w2"])};
static const float ad_b2[2 * AD_NFEAT] = {carr(P["b2"])};

#endif /* ANOMALY_MODEL_H_ */
""", encoding="utf-8")


def write_test_data(src: Path, sc: dict, expect: list[tuple]):
    S, T = sc["temp"].shape
    W = T // F.WINDOW

    def rows(a: np.ndarray, k: int) -> str:
        return ",\n".join("\t\t" + ", ".join(map(str, a[i:i + k].tolist())) for i in range(0, len(a), k))

    (src / "test_data.h").write_text(f"""/* Generated by ml/train.py - do not edit. */
#ifndef TEST_DATA_H_
#define TEST_DATA_H_
#include <stdint.h>

#define TEST_SCENARIOS {S}
#define TEST_N_SAMPLES {T}
#define TEST_N_WINDOWS {W}

extern const char *const test_name[TEST_SCENARIOS];
extern const uint32_t test_start_sec[TEST_SCENARIOS];              /* time of day of sample 0 [s] */
extern const int16_t test_temp_centi[TEST_SCENARIOS][TEST_N_SAMPLES]; /* 1 Hz [0.01 degC] */
extern const uint8_t test_label[TEST_SCENARIOS][TEST_N_WINDOWS];   /* ground truth per window */
/* Python reference result over judged windows: TP, FP, TN, FN, FNV-1a hash of all score bits */
extern const uint32_t test_expect[TEST_SCENARIOS][5];

#endif /* TEST_DATA_H_ */
""", encoding="utf-8")
    names = ", ".join(f'"{n}"' for n in sc["names"])
    temps = ",\n".join("\t{\n" + rows(sc["temp"][i], 24) + "\n\t}" for i in range(S))
    labels = ",\n".join("\t{\n" + rows(sc["label"][i], 48) + "\n\t}" for i in range(S))
    exp = ",\n".join("\t{" + ", ".join(f"{v}u" for v in e[:4]) + f", 0x{e[4]:08X}u}}" for e in expect)
    (src / "test_data.c").write_text(f"""/* Generated by ml/train.py from data.showcase() - do not edit. */
#include "test_data.h"

const char *const test_name[TEST_SCENARIOS] = {{{names}}};
const uint32_t test_start_sec[TEST_SCENARIOS] = {{{", ".join(f"{int(s)}u" for s in sc["sec0"])}}};

const int16_t test_temp_centi[TEST_SCENARIOS][TEST_N_SAMPLES] = {{
{temps}
}};

const uint8_t test_label[TEST_SCENARIOS][TEST_N_WINDOWS] = {{
{labels}
}};

const uint32_t test_expect[TEST_SCENARIOS][5] = {{
{exp}
}};
""", encoding="utf-8")


def plot_showcase(path: Path, sc: dict, r: dict, thr: tuple):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    S = len(sc["names"])
    fig, axs = plt.subplots(S, 1, figsize=(16, 4.2 * S))
    for i, ax in enumerate(np.atleast_1d(axs)):
        x = sc["temp"][i] / 100
        t = np.arange(len(x)) / 3600
        tw = (np.arange(len(r["phase"][i])) + 1) * F.WINDOW / 3600
        ax.plot(t, x, lw=0.5, color="tab:blue")
        for a, b in runs(sc["label"][i].astype(bool)):
            ax.axvspan(a / 60, b / 60, color="orange", alpha=0.3, lw=0)
        ph = r["phase"][i]
        ax.axvspan(0, (ph == 0).sum() / 60, color="grey", alpha=0.4, lw=0)
        first_full = np.argmax(ph == 2) / 60 if (ph == 2).any() else None
        if first_full:
            ax.axvline(first_full, color="green", ls="--", lw=1)
        al = r["alarm"][i]
        xm = x.reshape(-1, F.WINDOW).mean(1)
        ax.plot(tw[al], xm[al], "r.", ms=3)
        ax.set_title(f"{sc['names'][i]}: grey = recognising ({F.RECOG} min), green line = daily profile learned (FULL), "
                     f"orange = true anomaly, red = alarm (thresholds {thr[0]:.2f} / {thr[1]:.2f})", fontsize=9)
        ax.set_xlabel("hours since the sensor was installed")
        ax.set_ylabel("degC")
        ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=9001)
    ap.add_argument("--cache", type=Path, default=ROOT / "data" / "cache")
    ap.add_argument("--hidden", type=int, nargs="+", default=[8, 12, 16, 24, 32])
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--steps", type=int, default=4000)
    ap.add_argument("--batch", type=int, default=65536)
    ap.add_argument("--lr", type=float, default=5e-3)
    ap.add_argument("--nll-tol", type=float, default=0.01, help="pick the smallest H within this of the best val NLL")
    ap.add_argument("--fw", type=Path, default=ROOT / "src", help="where anomaly_model.h is written")
    ap.add_argument("--selftest", type=Path, default=ROOT / "selftest" / "src", help="where test_data.{c,h} go")
    ap.add_argument("--out", type=Path, default=ROOT / "artifacts")
    a = ap.parse_args()
    a.out.mkdir(parents=True, exist_ok=True)
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    print(f"data (seed {a.seed}, {DAYS}-day deployments of {', '.join(D.ENVS)}):")
    tr_ds, va_ds, dv_ds, te_ds = (load(s, a.seed, a.cache) for s in SPLITS)
    t0 = time.time()
    feats = []
    for ds in (tr_ds, va_ds):
        r = F.run(ds, ds["sec0"], keep=True)
        mk = r["phase"] > 0
        feats.append((r["ctx"][mk], r["y"][mk]))
    (ctr, ytr), (cva, yva) = feats
    print(f"  features: train {len(ctr)} windows, val {len(cva)} ({time.time() - t0:.0f}s)")
    norm = (ctr.mean(0).astype(np.float64), np.maximum(ctr.std(0), 1e-3).astype(np.float64),
            ytr.mean(0).astype(np.float64), np.maximum(ytr.std(0), 1e-3).astype(np.float64))
    g = lambda x, mu, sd: torch.tensor((x - mu) / sd, dtype=torch.float32, device=dev)
    tr = (g(ctr, norm[0], norm[1]), g(ytr, norm[2], norm[3]))
    va = (g(cva, norm[0], norm[1]), g(yva, norm[2], norm[3]))

    cands = [(h, 1000 * h + s) for h in a.hidden for s in range(a.seeds)]
    model = Candidates(cands).to(dev)
    t0 = time.time()
    best = train(model, tr, va, a.steps, a.lr, a.batch)
    print(f"trained {len(cands)} candidates from scratch on "
          f"{torch.cuda.get_device_name(0) if dev.type == 'cuda' else 'cpu'} in {time.time() - t0:.0f}s")
    per_h = {}
    for i, (h, _) in enumerate(cands):
        if h not in per_h or best[i] < best[per_h[h]]:
            per_h[h] = i
    gbest = min(best[i] for i in per_h.values())
    chosen_h = min(h for h, i in per_h.items() if best[i] <= gbest + a.nll_tol)
    ci = per_h[chosen_h]
    table = [dict(hidden=h, params=F.NCTX * h + h + 2 * F.NFEAT * h + 2 * F.NFEAT, val_nll=round(float(best[i]), 4),
                  chosen=h == chosen_h) for h, i in sorted(per_h.items())]
    for row in table:
        print(f"  H={row['hidden']:3d} params={row['params']:4d} val NLL={row['val_nll']:.4f}"
              f"{'   <- chosen (smallest within NLL tolerance)' if row['chosen'] else ''}")

    P = export_params(model, ci, chosen_h, norm)
    sub = slice(0, 200000)
    with torch.no_grad():                                          # export check: torch == deploy path
        mu, beta = model(va[0][sub])
        ymu, ysd = (torch.tensor(v, dtype=torch.float32, device=dev) for v in norm[2:])
        z = ((va[1][sub] - mu[ci]) * torch.exp2(beta[ci]))
        ref = (z * z).mean(1).cpu().numpy()
    dep = F.nn_score(P, cva[sub], yva[sub])
    export_err = float(np.max(np.abs(dep - ref) / np.maximum(ref, 1e-2)))

    rv = F.run(va_ds, va_ds["sec0"], P)                            # normal only -> no alarms, no feedback
    thr_q = tuple(float(f32(np.quantile(rv["score"][rv["phase"] == ph], 0.999))) for ph in (1, 2))
    print(f"thresholds from normal val streams only (0.999 quantile): BASIC {thr_q[0]:.3f} FULL {thr_q[1]:.3f}")
    grid = [float(f32(np.quantile(rv["score"][rv["phase"] == 1], q))) for q in (0.95, 0.97, 0.98, 0.99, 0.995, 0.999)]
    thr = calibrate(P, dv_ds, grid, thr_q[1])
    res = evaluate(te_ds, F.run(te_ds, te_ds["sec0"], P, thr))
    res_q = evaluate(te_ds, F.run(te_ds, te_ds["sec0"], P, thr_q))
    res_basic = evaluate(te_ds, F.run(te_ds, te_ds["sec0"], P, thr, learn=False))
    res_nogate = evaluate(te_ds, F.run(te_ds, te_ds["sec0"], P, thr, gate=False))

    sc = D.showcase()
    rs = F.run(F.window_stats(sc["temp"]), sc["sec0"], P, thr)
    expect, show = [], {}
    for i, name in enumerate(sc["names"]):
        mk, y, p = rs["phase"][i] > 0, sc["label"][i].astype(bool), rs["alarm"][i]
        e = (int((p & y & mk).sum()), int((p & ~y & mk).sum()), int((~p & ~y & mk).sum()), int((~p & y & mk).sum()),
             fnv1a(rs["score"][i][mk]))
        expect.append(e)
        show[str(name)] = dict(tp=e[0], fp=e[1], tn=e[2], fn=e[3], accuracy=round((e[0] + e[2]) / int(mk.sum()), 4),
                               score_hash=f"0x{e[4]:08X}")
    a.fw.mkdir(parents=True, exist_ok=True)
    a.selftest.mkdir(parents=True, exist_ok=True)
    n_params = int(sum(v.size for v in P.values()))
    write_model_header(a.fw / "anomaly_model.h", P, thr,
                       f"H={chosen_h}, {n_params} params, trained from scratch on {len(tr_ds['sec0'])} normal streams")
    write_test_data(a.selftest, sc, expect)
    np.savez(a.out / "showcase.npz", score=rs["score"], phase=rs["phase"], alarm=rs["alarm"])
    np.savez(a.out / "model.npz", thr_basic=np.float32(thr[0]), thr_full=np.float32(thr[1]), **P)
    plot_showcase(a.out / "showcase.png", sc, rs, thr)

    report = dict(model=dict(hidden=chosen_h, params=n_params, context=F.CONTEXT, features=F.FEATURES,
                             window_s=F.WINDOW, recognition_windows=F.RECOG, slots=F.SLOTS, threshold=thr,
                             threshold_rule="max window accuracy on labelled dev streams (iterated)",
                             export_rel_err=export_err, seed=a.seed),
                  candidates=table, test=res, test_normal_only_threshold=dict(threshold=thr_q, **res_q),
                  test_without_daily_profile=res_basic, test_without_alarm_gating=res_nogate, showcase=show)
    (a.out / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    print(f"\nchosen H={chosen_h}  params={n_params}  thresholds BASIC {thr[0]:.3f} FULL {thr[1]:.3f}"
          f"  (torch->deploy max rel err {export_err:.1e})")
    print(f"test ({len(te_ds['sec0'])} deployments x {DAYS} days, {res['windows']} judged windows, "
          f"{res['tp'] + res['fn']} anomalous): accuracy={res['accuracy']} balanced={res['balanced_accuracy']} "
          f"precision={res['precision']} recall={res['recall']} F1={res['f1']} AUC={res['roc_auc']}")
    for k, v in res["per_phase"].items():
        print(f"  {k:5s}: windows={v['windows']:6d} accuracy={v['accuracy']} recall={v['recall']} FPR={v['false_positive_rate']}")
    print("  per space:", {k: v["accuracy"] for k, v in res["per_space"].items()})
    print("  per day:", res["accuracy_per_day"])
    print("  recall per type:", res["recall_per_type"])
    print(f"  events detected {res['events_detected']}/{res['events']}, false-alarm runs/day {res['false_alarm_runs_per_day']}")
    print(f"normal-only thresholds {thr_q[0]:.3f}/{thr_q[1]:.3f}: accuracy={res_q['accuracy']} recall={res_q['recall']} "
          f"FA runs/day={res_q['false_alarm_runs_per_day']}")
    print(f"without the daily profile (BASIC only): accuracy={res_basic['accuracy']} recall={res_basic['recall']} "
          f"FA runs/day={res_basic['false_alarm_runs_per_day']}")
    print(f"without alarm gating of first learning: accuracy={res_nogate['accuracy']} recall={res_nogate['recall']} "
          f"FA runs/day={res_nogate['false_alarm_runs_per_day']}")
    print("showcase:", show)


if __name__ == "__main__":
    main()
