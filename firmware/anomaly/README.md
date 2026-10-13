# On-device temperature anomaly model

Recognise-then-judge anomaly detector for a 1 Hz temperature stream. Trained in
PyTorch, deployed as a 264-parameter float32 network in plain C (no libm, no
heap, ~1.3 KB of state). `firmware/matter/judge_dk` runs it on the nRF54LM20-DK
against the readings it pulls from the Matter temperature sensor.

```
sample (1 Hz) ──ad_feed──▶ 60-sample window ──ad_run_inference──▶ {score, phase, anomaly}
```

| Phase | When | Judged against |
|---|---|---|
| `LEARNING` | first **5 min** after the first reading | nothing (recognising level, swing, noise) |
| `BASIC` | from minute 6 | the recognised level `L0` |
| `FULL` | once the current time of day has been seen on an earlier day | the learned 96 x 15 min daily profile |

Alarm when `score >= threshold` of the phase (`AD_THR_BASIC` / `AD_THR_FULL`
in `src/anomaly_model.h`). The daily profile postpones learning a slot once if
that slot raised an alarm, so a first-day incident is not learned as normal.

## Layout

| Path | Content |
|---|---|
| `src/anomaly.{c,h}` | C runtime shared by `selftest/` and `matter/judge_dk` |
| `src/anomaly_model.h` | **generated** weights, thresholds, polynomial constants (`ml/train.py`) |
| `ml/features.py` | bit-exact float32 mirror of `anomaly.c`; every constant lives here |
| `ml/data.py` | simulated spaces (room, office, fridge, freezer, sauna) with physical and sensor faults |
| `ml/train.py` | train, calibrate thresholds, evaluate, export header + test data + report |
| `ml/detect.py` | run the exported model over a CSV (`timestamp,temperature[,anomaly]`) |
| `ml/c_check.py` | host parity check (needs clang) + Cortex-M33 footprint |
| `selftest/` | standalone Zephyr app: replays 3 embedded 3-day deployments, checks every score bit against Python, times the detector |
| `artifacts/` | `report.json` (metrics), `model.npz`, `showcase.{npz,png}` |
| `data/` | simulation cache and showcase CSVs (git-ignored, regenerated on demand) |

## Results (seed 9001, 5 min recognition)

Test: 100 deployments x 7 days, 1,007,500 judged windows.

| | accuracy | recall | precision | FPR | AUC |
|---|---|---|---|---|---|
| all | 0.9548 | 0.716 | 0.702 | 0.0230 | 0.951 |
| BASIC | 0.9095 | 0.312 | | 0.0382 | |
| FULL | 0.9630 | 0.793 | | 0.0230 | |

1290 / 1447 incidents detected, 2.1 false-alarm runs per day. Sensor faults
(spike, stuck, noise) are caught at ~100 %; slow physical faults in the first
day (BASIC) are the weak spot — the daily profile is what lifts recall.
Shortening recognition from 10 to 5 minutes cost nothing measurable
(0.9550 -> 0.9548).

## Retrain

```powershell
cd firmware/anomaly
uv sync                         # or: python -m venv .venv; pip install numpy torch matplotlib
uv run python ml/train.py       # ~10 min on CPU, seconds on a GPU
```

Writes `src/anomaly_model.h`, `selftest/src/test_data.{c,h}`, `artifacts/*`.
Any change to a constant in `ml/features.py` must be mirrored in
`src/anomaly.h`; the `#if` at the top of the generated header refuses to
compile otherwise.

```powershell
uv run python ml/detect.py data/showcase/sauna_50C.csv   # data/: uv run python ml/data.py
```

## Self-test on the DK

Plain Zephyr app (no Matter, no MCUboot), prints the replay of the three
embedded deployments and whether every score matches the Python reference.
It overwrites the Matter application; re-flash `matter/judge_dk` with
`--erase` and commission again afterwards.

```powershell
west build -b nrf54lm20dk/nrf54lm20b/cpuapp -d C:\ncs\tmp\adt firmware/anomaly/selftest
west flash -d C:\ncs\tmp\adt
```

## Time of day

The daily profile needs the time of day of each sample. The DK has no wall
clock, so `judge_dk` uses seconds since boot modulo 24 h: slot boundaries are
offset from real time but the profile is still 24 h periodic. If the fabric
ever provides time (Time Synchronization cluster), pass real seconds of day
to `ad_feed()` instead.
