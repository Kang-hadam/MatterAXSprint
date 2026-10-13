"""CSV -> anomaly alarms with the exported model (the computation the firmware runs, bit for bit).

The CSV is one sensor stream at 1 Hz from the moment the sensor was installed:
timestamp,temperature[,anomaly]. The first 5 minutes are recognised, every later minute is judged;
recognition, phase changes and alarms are printed, plus window accuracy if an anomaly column exists.
Usage (from firmware/anomaly): uv run python ml/detect.py data/showcase/sauna_50C.csv [--model artifacts/model.npz]
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

import features as F

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("csv", type=Path)
    ap.add_argument("--model", type=Path, default=ROOT / "artifacts" / "model.npz")
    a = ap.parse_args()
    z = np.load(a.model)
    P = {k: z[k] for k in ("w1", "b1", "w2", "b2")}
    thr = (float(z["thr_basic"]), float(z["thr_full"]))
    temp, sec0, t0, names = F.read_csv(a.csv)
    n = len(temp) // F.WINDOW * F.WINDOW
    if n <= F.RECOG * F.WINDOW:
        raise SystemExit(f"need more than {F.RECOG} minutes of data")
    r = F.run(F.window_stats(temp[:n][None]), [sec0], P, thr)
    ph, sc, al = r["phase"][0], r["score"][0], r["alarm"][0]
    xm = temp[:n].reshape(-1, F.WINDOW)[:, -1] / 100

    def when(k: int) -> str:
        return str(t0 + np.timedelta64(int((k + 1) * F.WINDOW - 1), "s")).replace("T", " ")

    print(f"{a.csv.name}: {n // F.WINDOW} minutes from {str(t0).replace('T', ' ')}, thresholds BASIC {thr[0]:.3f} / FULL {thr[1]:.3f}")
    kb = int(np.argmax(ph == 1))
    print(f"{when(kb)}  recognised {float(r['level'][0]):.2f} C after {F.RECOG} min -> BASIC: judged against the recognised level")
    if (ph == 2).any():
        print(f"{when(int(np.argmax(ph == 2)))}  daily profile learned -> FULL: judged against the time-of-day profile")
    d = np.diff(np.r_[0, al.astype(np.int8), 0])
    for s, e in zip(np.flatnonzero(d == 1), np.flatnonzero(d == -1)):
        print(f"{when(s)}  ANOMALY  peak score {sc[s:e].max():8.1f}  {xm[s]:7.2f} C -> {xm[e - 1]:7.2f} C  "
              f"{e - s:4d} min  [{F.PHASES[ph[s]]}]")
    m = ph > 0
    print(f"judged {int(m.sum())} minutes, {int((d == 1).sum())} alarms ({int(al.sum())} anomalous minutes)")
    if names is not None:
        y = F.window_labels(names[:n])
        tp, fp = int((al & y & m).sum()), int((al & ~y & m).sum())
        tn, fn = int((~al & ~y & m).sum()), int((~al & y & m).sum())
        print(f"vs anomaly column: accuracy {(tp + tn) / int(m.sum()):.4f}  recall {tp / max(tp + fn, 1):.4f}  "
              f"precision {tp / max(tp + fp, 1):.4f}  (TP {tp} FP {fp} TN {tn} FN {fn})")


if __name__ == "__main__":
    main()
