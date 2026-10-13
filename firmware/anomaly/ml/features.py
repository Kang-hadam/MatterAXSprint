"""Streaming detector - float32 mirror of firmware/src/anomaly.c (same operations in the same order).

Every 60 s window gives six features: level (mean), slow level (10 min EMA of means), trend (mean - EMA of
earlier means) and log2 of the std, the max |dx| and the mean |dx|. The device first RECOGNISES its space:
  - first RECOG windows (5 min): recognised level L0, its swing (log2 std of the window means) and noise
    baselines (mean log2 std / max|dx| / mean|dx|)
  - from then on a daily profile of 96 slots x 15 min (slot mean m, day-to-day spread d, days learned n);
    the first learning of a slot is postponed once if the slot raised an alarm (accepted the second time,
    so recurring patterns such as defrost get learned), later days update it with a clipped running mean.
Every later window is judged relative to what was recognised: against L0 while its time of day is not
learned yet (BASIC), against the learned profile at that time of day afterwards (FULL).
ml/c_check.py checks the C build against this file bit for bit.

Layout in the repo (firmware/anomaly/): ml/ this package, src/ the C runtime + generated model header,
selftest/ a standalone Zephyr replay of the embedded showcase deployments, artifacts/ report and weights.
"""
from __future__ import annotations

import csv
from pathlib import Path

import numpy as np

f32 = np.float32
WINDOW, RECOG, SLOTS, SLOT_SEC, NMAX, MINCNT, DAY_WIN, DAY = 60, 5, 96, 900, 7, 8, 1440, 86400
EMA_ALPHA, EPS_VAR, EPS_RNG, EPS_SL, EPS_D, DFLOOR, CLIP_K = (f32(v) for v in (0.1, 1e-4, 1e-2, 1e-2, 1e-2, 0.1, 3.0))
FEATURES = ("level", "slow", "trend", "lstd", "ldmax", "ldabs")
CONTEXT = ("ready", "day1", "lslope", "slope_dir", "lspread", "days", "noise", "swing")
NFEAT, NCTX = len(FEATURES), len(CONTEXT)
PHASES = ("LEARNING", "BASIC", "FULL")
LOG2_C = (1.44182586, -0.708682819, 0.415424374, -0.194425906, 0.0458870086)  # log2(1+m)=m*q(m)
EXP2_C = (0.693018698, 0.241404294, 0.0520748833, 0.0134929069)              # 2^f=1+f*r(f)
HALF = f32(0.5)
INV_W, INV_R, INV_SLOT, INV_DAY, INV_NMAX, INV_F = (f32(1) / f32(v) for v in (WINDOW, RECOG, SLOT_SEC, DAY_WIN, NMAX, NFEAT))


def _horner(x: np.ndarray, coefs) -> np.ndarray:
    p = np.full_like(x, f32(coefs[-1]))
    for c in coefs[-2::-1]:
        p = p * x + f32(c)
    return p


def log2_fast(x: np.ndarray) -> np.ndarray:
    x = np.ascontiguousarray(x, dtype=f32)
    u = x.view(np.uint32)
    e = ((u >> 23).astype(np.int32) - 127).astype(f32)
    m = ((u & 0x007FFFFF) | 0x3F800000).astype(np.uint32).view(f32) - f32(1)
    return e + m * _horner(m, LOG2_C)


def exp2_fast(x: np.ndarray) -> np.ndarray:
    x = np.clip(np.asarray(x, dtype=f32), f32(-60), f32(60))
    fl = np.floor(x)
    f = x - fl
    p = np.ascontiguousarray(f32(1) + f * _horner(f, EXP2_C), dtype=f32)
    return (p.view(np.int32) + fl.astype(np.int32) * (1 << 23)).view(f32)


def window_stats(temp: np.ndarray) -> dict:
    """Window features of streams of centi-degC samples [N, T] (T a multiple of 60) -> [N, W] arrays."""
    temp = np.atleast_2d(temp)
    N, W = len(temp), temp.shape[1] // WINDOW
    out = {k: np.empty((N, W), f32) for k in ("mean", "lstd", "ldmax", "ldabs")}
    for n in range(N):
        x = temp[n, :W * WINDOW].astype(f32) / f32(100)
        xw = x.reshape(W, WINDOW)
        dx = xw - xw[:, :1]
        s = np.cumsum(dx, 1, dtype=f32)[:, -1]               # sequential sums, as in C
        ss = np.cumsum(dx * dx, 1, dtype=f32)[:, -1]
        a = np.abs(np.diff(x, prepend=x[0])).reshape(W, WINDOW)
        dsum = np.cumsum(a, 1, dtype=f32)[:, -1]
        mm = s * INV_W
        out["mean"][n] = xw[:, 0] + mm
        var = ss * INV_W - mm * mm
        var = np.where(var < 0, f32(0), var)
        out["lstd"][n] = HALF * log2_fast(var + EPS_VAR)
        out["ldmax"][n] = log2_fast(a.max(1) + EPS_RNG)
        out["ldabs"][n] = log2_fast(dsum * INV_W + EPS_RNG)
    return out


def nn_score(P: dict, c: np.ndarray, y: np.ndarray) -> np.ndarray:
    """Deploy-exact network and score for context rows c [n, NCTX] and relative features y [n, NFEAT]."""
    w1, b1, w2, b2 = P["w1"], P["b1"], P["w2"], P["b2"]
    n, H = len(c), len(b1)
    a = np.broadcast_to(b1, (n, H)).copy()
    for i in range(NCTX):
        a = a + w1[:, i] * c[:, i:i + 1]
    h = np.where(a > 0, a, f32(0))
    mu = np.broadcast_to(b2[:NFEAT], (n, NFEAT)).copy()
    be = np.broadcast_to(b2[NFEAT:], (n, NFEAT)).copy()
    for j in range(H):
        hj = h[:, j:j + 1]
        mu = mu + w2[:NFEAT, j] * hj
        be = be + w2[NFEAT:, j] * hj
    acc = np.zeros(n, f32)
    for k in range(NFEAT):
        z = (y[:, k] - mu[:, k]) * exp2_fast(be[:, k])
        acc = acc + z * z
    return acc * INV_F


def _finalize(idx, cur, acc_sum, acc_cnt, acc_alarm, m, d, meta, floor):
    """Learn the slots that just ended (streams idx) into the daily profile, as ad_finalize_slot()."""
    idx = idx[acc_cnt[idx] >= MINCNT]
    if not idx.size:
        return
    s = cur[idx]
    t = acc_sum[idx] / acc_cnt[idx].astype(f32)
    mt = meta[idx, s]
    n = (mt & 15).astype(np.int64)
    first = n == 0
    learn = first & (~acc_alarm[idx] | ((mt & 128) != 0))
    li, ls = idx[learn], s[learn]
    m[li, ls], d[li, ls], meta[li, ls] = t[learn], f32(0), 1
    meta[idx[first & ~learn], s[first & ~learn]] |= 128
    up = ~first
    ui, us, un = idx[up], s[up], n[up]
    if ui.size:
        dv, mv = d[ui, us], m[ui, us]
        lim = CLIP_K * np.maximum(dv, floor[ui])
        e = t[up] - mv
        e = np.where(e > lim, lim, np.where(e < -lim, -lim, e))
        d[ui, us] = dv + (np.abs(e) - dv) / np.minimum(un, NMAX).astype(f32)
        m[ui, us] = mv + e / np.minimum(un + 1, NMAX).astype(f32)
        meta[ui, us] = np.minimum(un + 1, NMAX)


def run(st: dict, sec0, model: dict | None = None, thr=(np.inf, np.inf), keep: bool = False,
        learn: bool = True, gate: bool = True) -> dict:
    """Stream all windows through the detector (vectorised over streams).
    thr = (BASIC threshold, FULL threshold). model None -> no scores and no alarms (training features).
    keep -> also return context and features. learn False -> the daily profile is never learned (BASIC
    only); gate False -> alarms never postpone learning (ablations; the firmware does both)."""
    mean, lstd, ldmax, ldabs = st["mean"], st["lstd"], st["ldmax"], st["ldabs"]
    N, W = mean.shape
    rows = np.arange(N)
    sec0 = np.asarray(sec0, np.int64).reshape(N)
    thr_b, thr_f = f32(thr[0]), f32(thr[1])
    ema, L0, Bs, Bm, Ba, rs, rq, swing = (np.zeros(N, f32) for _ in range(8))
    floor = np.full(N, DFLOOR, f32)
    m, d, meta = np.zeros((N, SLOTS), f32), np.zeros((N, SLOTS), f32), np.zeros((N, SLOTS), np.uint8)
    cur, acc_sum = np.full(N, -1, np.int64), np.zeros(N, f32)
    acc_cnt, acc_alarm = np.zeros(N, np.int64), np.zeros(N, bool)
    phase, score, alarm = np.zeros((N, W), np.uint8), np.zeros((N, W), f32), np.zeros((N, W), bool)
    ctx = np.zeros((N, W, NCTX) if keep else (0, 0, NCTX), f32)
    ys = np.zeros((N, W, NFEAT) if keep else (0, 0, NFEAT), f32)
    for k in range(W):
        mk = mean[:, k]
        if k == 0:
            ema = mk.copy()
        trend = mk - ema
        ema = ema + EMA_ALPHA * (mk - ema)
        tau = (sec0 + k * WINDOW + WINDOW - 1) % DAY        # time of day of the window's last sample
        slot = tau // SLOT_SEC
        chg = slot != cur
        fin = np.flatnonzero(chg & (cur >= 0))
        if fin.size and learn:
            _finalize(fin, cur, acc_sum, acc_cnt, acc_alarm, m, d, meta, floor)
        cur = np.where(chg, slot, cur)
        acc_sum = np.where(chg, f32(0), acc_sum)
        acc_cnt = np.where(chg, 0, acc_cnt)
        acc_alarm = np.where(chg, False, acc_alarm)
        al = np.zeros(N, bool)
        if k < RECOG:
            if k == 0:
                L0 = mk.copy()                                 # first window mean, the recognition origin
            dm = mk - L0
            rs, rq = rs + dm, rq + dm * dm
            Bs, Bm, Ba = Bs + lstd[:, k], Bm + ldmax[:, k], Ba + ldabs[:, k]
            if k == RECOG - 1:
                mr = rs * INV_R
                var = rq * INV_R - mr * mr
                var = np.where(var < 0, f32(0), var)
                L0, swing = L0 + mr, HALF * log2_fast(var + EPS_VAR)
                Bs, Bm, Ba = Bs * INV_R, Bm * INV_R, Ba * INV_R
                floor = np.maximum(DFLOOR, exp2_fast(Bs))
        else:
            q = tau - SLOT_SEC // 2
            q = np.where(q < 0, q + DAY, q)
            s0 = q // SLOT_SEC
            s1 = np.where(s0 + 1 == SLOTS, 0, s0 + 1)
            f = (q % SLOT_SEC).astype(f32) * INV_SLOT
            n0, n1 = meta[rows, s0] & 15, meta[rows, s1] & 15
            ready = (n0 > 0) & (n1 > 0)
            m0, d0 = m[rows, s0], d[rows, s0]
            slope = np.where(ready, m[rows, s1] - m0, f32(0))
            ref = np.where(ready, m0 + f * slope, L0)
            dd = np.where(ready, d0 + f * (d[rows, s1] - d0), f32(0))
            nn = np.where(ready, np.minimum(n0, n1), 0).astype(f32)
            asl = np.abs(slope)
            c = np.stack([ready.astype(f32), np.full(N, f32(min(k, DAY_WIN)) * INV_DAY, f32),
                          log2_fast(asl + EPS_SL), slope / (asl + EPS_SL), log2_fast(dd + EPS_D),
                          nn * INV_NMAX, Bs, swing], 1)
            y = np.stack([mk - ref, ema - ref, trend, lstd[:, k] - Bs, ldmax[:, k] - Bm, ldabs[:, k] - Ba], 1)
            phase[:, k] = np.where(ready, 2, 1)
            if model is not None:
                score[:, k] = nn_score(model, c, y)
                al = score[:, k] >= np.where(ready, thr_f, thr_b)
                alarm[:, k] = al
            if keep:
                ctx[:, k], ys[:, k] = c, y
        acc_sum = acc_sum + mk
        acc_cnt = acc_cnt + 1
        acc_alarm = acc_alarm | (al & gate)
    out: dict = dict(phase=phase, score=score, alarm=alarm, level=L0)
    if keep:
        out.update(ctx=ctx, y=ys)
    return out


def read_csv(path: Path):
    """timestamp ('YYYY-MM-DD HH:MM:SS'),temperature [degC][,anomaly] at 1 Hz from installation ->
    (centi-degC int16 [T], second of day of the first sample, first timestamp, anomaly names or None)."""
    with open(path, newline="", encoding="utf-8") as fh:
        rows = list(csv.reader(fh))
    head, rows = [h.strip().lower() for h in rows[0]], [r for r in rows[1:] if r]
    ts = np.array([r[0].strip().replace(" ", "T") for r in rows], dtype="datetime64[s]")
    if len(ts) > 1 and np.any(np.diff(ts).astype(np.int64) != 1):
        raise SystemExit(f"{path}: needs a gap-free 1 Hz stream (one row per second)")
    temp = np.round(np.array([float(r[1]) for r in rows]) * 100).astype(np.int16)
    sec0 = int((ts[0] - ts[0].astype("datetime64[D]")).astype(np.int64))
    names = np.array([r[2].strip() if len(r) > 2 else "" for r in rows]) if "anomaly" in head else None
    return temp, sec0, ts[0], names


def window_labels(names: np.ndarray) -> np.ndarray:
    """Per-sample anomaly names -> window label (spike anywhere, or >= half of the window anomalous)."""
    w = names[:len(names) // WINDOW * WINDOW].reshape(-1, WINDOW)
    return (w == "spike").any(1) | ((w != "").sum(1) >= WINDOW // 2)
