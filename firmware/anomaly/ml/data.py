"""Synthetic 1 Hz temperature streams from five kinds of temperature-controlled spaces.

A stream is one sensor deployment: it starts at a random time of day and runs for several days, so the
detector has to recognise the space from scratch. Normal behaviour comes from a two-node RC thermal model
(air + thermal mass) with a heating or cooling thermostat (schedule, hysteresis, minimum cycle time),
ambient temperature, doors, sun, occupants, cooking and freezer defrost, read through a lagging, noisy
sensor. Physical faults run inside the model and are labelled where the 10 min average deviates from an
anomaly-free twin by >= LABEL_DEV of the space; sensor faults are applied to the measurement.

CLI: writes the three showcase deployments (the ones embedded in the firmware) as CSV examples.
"""
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

DAY, HOUR, MIN = 86400, 3600, 60
BURN_IN = 12 * HOUR
ENVS = ("room", "office", "fridge", "freezer", "sauna")
COLD = (False, False, True, True, False)                  # cooled by a compressor instead of heated
LABEL_DEV = (1.0, 1.0, 1.5, 2.0, 3.0)                    # degC from the anomaly-free twin = anomalous
TYPES = ("door_open", "control_fail", "control_stuck", "heat_event", "setpoint_fault",
         "spike", "stuck", "noise", "offset")
PHYS = TYPES[:5]
DUR = {"door_open": (5 * MIN, 60 * MIN), "control_fail": (60 * MIN, 180 * MIN),
       "control_stuck": (30 * MIN, 90 * MIN), "heat_event": (4 * MIN, 10 * MIN),
       "setpoint_fault": (60 * MIN, 150 * MIN), "spike": (1, 3), "stuck": (15 * MIN, 60 * MIN),
       "noise": (10 * MIN, 30 * MIN), "offset": (30 * MIN, 90 * MIN)}
EVENTS_PER_DAY = 2
FIRST_EVENT = HOUR                                        # the recognition hour stays normal
BASE_DATE = np.datetime64("2026-01-05T00:00:00")


def sample_params(env: int, rng: np.random.Generator) -> dict:
    u = rng.uniform
    p: dict = dict(env=env, kam=1 / u(900, 1800), kma=1 / u(10000, 20000), kmo=1 / u(80000, 140000),
             lag=u(30, 120), noise=u(0.01, 0.04), duty=u(0.45, 0.65), outdoor=False, sun=None,
             occ=None, cooking=False, airing=None, defrost=None)
    name = ENVS[env]
    if name == "room":
        p.update(outdoor=True, kao=u(0.7, 1.4) / 18000, hyst=u(0.2, 0.4), hold=240,
                 sched=[(6 + u(-.5, .5), u(20.5, 22), 10), (8.5 + u(-.5, .5), u(19.5, 21), 15),
                        (17 + u(-.5, .5), u(21, 23), 15), (22.5 + u(-.5, .5), u(17.5, 19.5), 15)],
                 sun=(5.0, 13.5, 1.6), occ=(1.0, ((6, 8.5), (17, 23.5))), cooking=True,
                 doors=(4, (7, 22), (40, 150), (10, 10)), airing=(0.7, (7, 8), (5 * MIN, 12 * MIN), 12))
    elif name == "office":
        p.update(outdoor=True, kao=u(0.7, 1.4) / 18000, hyst=u(0.3, 0.5), hold=240,
                 sched=[(7 + u(-.5, .5), u(20, 22), 10), (19 + u(-1, 1), u(15, 17.5), 10)],
                 sun=(4.0, 13.0, 2.0), occ=(u(1.5, 3), ((8, 18),)),
                 doors=(10, (7.5, 18.5), (30, 120), (6, 6)), airing=(0.3, (11.5, 13.5), (5 * MIN, 15 * MIN), 10))
    elif name == "fridge":
        p.update(kao=u(0.7, 1.4) / 30000, hyst=u(0.8, 1.5), hold=300, sched=[(0.0, u(2, 6), 0)],
                 doors=(15, "meals", (10, 60), (20, 40)))
    elif name == "freezer":
        iv = float(rng.choice([8, 12]))
        p.update(kao=u(0.7, 1.4) / 40000, hyst=u(1, 2), hold=300, sched=[(0.0, u(-22, -16), 0)],
                 doors=(5, (7, 22), (10, 40), (15, 30)), defrost=(iv, u(0, iv), u(20, 30) * MIN, u(40, 70)))
    else:
        o, c, lv = 9 + u(-1, 1), 22 + u(-1, 1), u(45, 90)
        p.update(kao=u(0.7, 1.4) / 6000, hyst=u(1.5, 3), hold=120,
                 sched=[(o, lv, 10), (c, lv - u(3, 10), 10)], doors=(25, (o + .5, c - .5), (5, 30), (4, 8)))
    return p


def add(arr: np.ndarray, a: float, dur: float, val: float):
    """arr[minute] += val * share of that minute covered by [a, a + dur) (array seconds)."""
    a, b = max(a, 0.0), min(a + dur, len(arr) * MIN)
    if b <= a:
        return
    m0, m1 = int(a // MIN), int((b - 1e-9) // MIN)
    fr = np.ones(m1 - m0 + 1)
    fr[0] -= (a - m0 * MIN) / MIN
    fr[-1] -= ((m1 + 1) * MIN - b) / MIN
    arr[m0:m1 + 1] += val * fr


def minutes(arr: np.ndarray, a: float, dur: float) -> slice:
    a, b = max(a, 0.0), min(a + dur, len(arr) * MIN)
    return slice(int(a // MIN), int(np.ceil(b / MIN))) if b > a else slice(0, 0)


def drivers(p: dict, sec0: int, days: int, rng: np.random.Generator) -> dict:
    """Per-minute drivers of one stream, burn-in included: ambient and setpoint [degC], gain [degC/s],
    air-exchange multiplier, controller override (0 auto, 1 forced off, 2 forced on)."""
    M = (BURN_IN + days * DAY) // MIN
    clock = np.arange(M) * MIN - BURN_IN + sec0          # seconds since midnight of the first day
    hour = (clock % DAY) / HOUR
    cday = clock // DAY + 1                               # calendar day index, >= 0
    nd = int(cday[-1]) + 1
    u = rng.uniform
    knots = (np.arange(nd + 1) - 1) * DAY + DAY // 2     # noon of each calendar day
    if p["outdoor"]:
        base, amp, peak = u(-5, 8, nd + 1), u(2, 6, nd + 1), 15
    else:
        base, amp, peak = u(19, 25) + u(-1, 1, nd + 1), u(0.3, 1.5, nd + 1), 16
    tamb = np.interp(clock, knots, base) + np.interp(clock, knots, amp) * np.cos(2 * np.pi * (hour - peak) / 24)

    sched = p["sched"]
    setp = np.full(M, float(sched[-1][1]))
    for h0, level, jit in sched if len(sched) > 1 else ():
        setp = np.where(hour >= h0 + u(-jit, jit, nd)[cday] / 60, level, setp)

    gain = np.zeros(M)
    if p["sun"]:
        a, c, w = p["sun"]
        gain += a * u(0, 1, nd)[cday] ** 1.5 * np.exp(-0.5 * ((hour - c) / w) ** 2)
    if p["occ"]:
        g, spans = p["occ"]
        gain += g * np.any([(hour >= s) & (hour < e) for s, e in spans], axis=0)
    loss, force = np.ones(M), np.zeros(M, np.int8)

    def at(c: int, h: float) -> float:                    # array second of clock hour h on calendar day c
        return (c - 1) * DAY + h * HOUR - sec0 + BURN_IN

    n_doors, hours, dur, mult = p["doors"]
    for c in range(nd):
        if p["cooking"]:
            add(gain, at(c, 18.25 + rng.normal(0, 0.33)), u(25, 50) * MIN, 5.0)
        for _ in range(rng.poisson(n_doors)):
            if hours != "meals":
                h = u(*hours)
            elif rng.random() < 0.6:
                h = rng.choice([7.5, 12.5, 19.5]) + rng.normal(0, 0.7)
            else:
                h = u(6, 23)
            add(loss, at(c, h), u(*dur), u(*mult) - 1)
        if p["airing"] and rng.random() < p["airing"][0]:
            _, hrs, dr, m = p["airing"]
            add(loss, at(c, u(*hrs)), u(*dr), m - 1)
        if p["defrost"]:
            iv, off, dr, g = p["defrost"]
            for j in range(int(24 / iv)):
                add(gain, at(c, off + j * iv), dr, g)
                force[minutes(force, at(c, off + j * iv), dr)] = 1
    return dict(tamb=tamb, setp=setp, gain=gain / HOUR, loss=loss, force=force)


def apply_fault(drv: dict, ev: tuple, env: int, rng: np.random.Generator):
    """Physical fault (type, start [stream s], duration [s][, magnitude]) on a copy of the drivers."""
    typ, s, dur = ev[:3]
    mag = ev[3] if len(ev) > 3 else None
    a, cold = s + BURN_IN, COLD[env]
    if typ == "door_open":
        add(drv["loss"], a, dur, (mag or rng.uniform(*((20, 40) if cold else (8, 15)))) - 1)
    elif typ == "control_fail":
        drv["force"][minutes(drv["force"], a, dur)] = 1
    elif typ == "control_stuck":
        drv["force"][minutes(drv["force"], a, dur)] = 2
    elif typ == "heat_event":
        add(drv["gain"], a, dur, (mag or rng.uniform(*((30, 60) if cold else (80, 200)))) / HOUR)
    else:
        off = mag if mag is not None else rng.choice([-1, 1]) * rng.uniform(2.5, 5) * LABEL_DEV[env]
        drv["setp"][minutes(drv["setp"], a, dur)] += off


def apply_sensor(x: np.ndarray, ev: tuple, env: int, rng: np.random.Generator):
    """Sensor fault on one measured stream [centi-degC] in place."""
    typ, s, dur = ev[:3]
    mag, ld, sl = (ev[3] if len(ev) > 3 else None), LABEL_DEV[env], slice(s, s + dur)
    sign = rng.choice([-1, 1])
    if typ == "spike":
        x[sl] += int(round((mag or sign * rng.uniform(2, 8) * ld) * 100))
    elif typ == "stuck":
        x[sl] = x[s]
    elif typ == "noise":
        x[sl] += np.round(rng.normal(0, mag or rng.uniform(0.15, 0.4) * ld, dur) * 100).astype(np.int16)
    else:
        x[sl] += int(round((mag or sign * rng.uniform(1.5, 3.5) * ld) * 100))


def plan(days: int, env: int, rng: np.random.Generator) -> list[tuple]:
    """Non-overlapping faults (type, start [stream s], duration [s]); types cycle evenly."""
    T = days * DAY
    order = list(TYPES) * (days * EVENTS_PER_DAY // len(TYPES) + 1)
    rng.shuffle(order)
    events, busy = [], []
    for typ in order[:days * EVENTS_PER_DAY]:
        lo, hi = (20 * MIN, 40 * MIN) if typ == "heat_event" and COLD[env] else DUR[typ]
        for _ in range(200):
            dur = int(rng.uniform(lo, hi + 1))
            s = int(rng.uniform(FIRST_EVENT, T - dur - 2 * HOUR))
            b = (s - 90 * MIN, s + dur + 2 * HOUR)
            if all(b[1] <= x0 or b[0] >= x1 for x0, x1 in busy):
                busy.append(b)
                events.append((typ, s, dur))
                break
    return sorted(events, key=lambda e: e[1])


def thermal(drv: list[dict], prm: list[dict], noise_row: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """1 s Euler simulation of all streams at once -> sensor reading [centi-degC] after the burn-in.
    Streams with the same noise_row get identical sensor noise (anomaly / twin pairs)."""
    def col(k: str, dt: type = np.float64) -> np.ndarray:  # [minute, stream]
        return np.ascontiguousarray(np.stack([x[k] for x in drv], 1).astype(dt))

    tamb, setp, gain, loss = (col(k) for k in ("tamb", "setp", "gain", "loss"))
    force = col("force", np.int8)
    P = lambda k: np.array([p[k] for p in prm], np.float64)
    kam, kma, kmo, kao, q = P("kam"), P("kma"), P("kmo"), P("kao"), P("q")
    sgn = np.where([COLD[p["env"]] for p in prm], -1.0, 1.0)
    hyst, hold_s, inv_lag = P("hyst"), P("hold").astype(np.int32), 1 / P("lag")
    nsd = np.zeros(noise_row.max() + 1)
    nsd[noise_row] = P("noise")
    M, N = setp.shape
    ta, tm, ts = setp[0].copy(), setp[0].copy(), setp[0].copy()
    on, hold = np.zeros(N, bool), np.zeros(N, np.int32)
    out = np.empty((N, M * MIN - BURN_IN), np.int16)
    buf = np.empty((N, MIN))
    for mi in range(M):
        sp, tb, g, kl, f = setp[mi], tamb[mi], gain[mi], kao * loss[mi], force[mi]
        auto, forced = f == 0, f == 2
        for s in range(MIN):
            hold -= hold > 0
            e = sgn * (sp - ta)
            sw = (hold == 0) & np.where(on, e < -hyst, e > hyst)
            on ^= sw
            hold = np.where(sw, hold_s, hold)
            ta_new = ta + kam * (tm - ta) + kl * (tb - ta) + q * ((on & auto) | forced) + g
            tm += kma * (ta - tm) + kmo * (tb - tm)
            ta = ta_new
            ts += (ta - ts) * inv_lag
            buf[:, s] = ts
        a = mi * MIN - BURN_IN
        if a >= 0:
            nz = rng.normal(size=(len(nsd), MIN)) * nsd[:, None]
            out[:, a:a + MIN] = np.round((buf + nz[noise_row]) * 100)
    return out


def smooth(x: np.ndarray, w: int = 10 * MIN) -> np.ndarray:
    """Centred 10 min moving average: physical faults are labelled on the average temperature, so a
    shifted thermostat cycle alone does not count as an anomaly."""
    c = np.r_[0.0, np.cumsum(x, dtype=np.float64)]
    i = np.arange(len(x))
    lo, hi = np.maximum(i - w // 2, 0), np.minimum(i + w // 2, len(x))
    return (c[hi] - c[lo]) / (hi - lo)


def run(prm: list[dict], sec0: list[int], days: int, events: list[list], rng: np.random.Generator,
        keep_codes: bool = False) -> dict:
    """Simulate streams (with their anomaly-free twins when events are given) and label them."""
    clean = [drivers(p, s, days, rng) for p, s in zip(prm, sec0)]
    for p, d in zip(prm, clean):                          # controller sized for the worst steady duty
        sgn = -1.0 if COLD[p["env"]] else 1.0
        gap = max(float(np.max(sgn * (d["setp"] - d["tamb"]))), 1.0)
        p["q"] = sgn * (p["kao"] + p["kam"] * p["kmo"] / (p["kma"] + p["kmo"])) * gap / p["duty"]
    N, T, W = len(prm), days * DAY, days * DAY // MIN
    labelled = any(events)
    if labelled:
        bad = [{k: v.copy() for k, v in d.items()} for d in clean]
        for d, p, ev in zip(bad, prm, events):
            for e in ev:
                if e[0] in PHYS:
                    apply_fault(d, e, p["env"], rng)
        both = thermal(bad + clean, prm + prm, np.r_[np.arange(N), np.arange(N)], rng)
        meas, twin = both[:N].copy(), both[N:]
        del both
    else:
        meas = twin = thermal(clean, prm, np.arange(N), rng)
    code = np.zeros((N, T), np.uint8)
    for n in range(N if labelled else 0):
        env = prm[n]["env"]
        dev = np.abs(smooth(meas[n]) - smooth(twin[n])) >= LABEL_DEV[env] * 100
        for e in events[n]:
            typ, s, dur = e[:3]
            if typ in PHYS:                               # incident: from fault start until recovered
                rec = np.flatnonzero(~dev[s + dur:])
                end = s + dur + (rec[0] if rec.size else T - s - dur)
                mk = dev[s:end].copy()
                idx = np.flatnonzero(mk)
                gaps = np.diff(idx)
                for j in np.flatnonzero((gaps > 1) & (gaps <= 5 * MIN)):
                    mk[idx[j] + 1:idx[j + 1]] = True      # short interruptions belong to the incident
                code[n, s:end] = np.where(mk, TYPES.index(typ) + 1, code[n, s:end])
        for e in events[n]:
            if e[0] not in PHYS:
                apply_sensor(meas[n], e, env, rng)
                code[n, e[1]:e[1] + e[2]] = TYPES.index(e[0]) + 1
    cw = code.reshape(N, W, MIN)
    spike = (cw == TYPES.index("spike") + 1).any(2)
    counts = np.stack([(cw == t + 1).sum(2) for t in range(len(TYPES))], 2)
    label = spike | ((cw > 0).sum(2) >= MIN // 2)
    wtype = np.where(label, np.where(spike, TYPES.index("spike") + 1, counts.argmax(2) + 1), 0)
    out = dict(temp=meas, sec0=np.asarray(sec0, np.int64), env=np.array([p["env"] for p in prm], np.int8),
               label=label.astype(np.uint8), wtype=wtype.astype(np.uint8))
    if keep_codes:
        out["code"] = code
    return out


def simulate(n_per_env: int, days: int, seed, labelled: bool) -> dict:
    """n_per_env random deployments of every space; faults only when labelled."""
    rng = np.random.default_rng(seed)
    prm = [sample_params(e, rng) for e in range(len(ENVS)) for _ in range(n_per_env)]
    sec0 = [int(rng.integers(0, DAY)) for _ in prm]
    events = [plan(days, p["env"], rng) if labelled else [] for p in prm]
    return run(prm, sec0, days, events, rng)


# Showcase deployments embedded in the firmware: (name, space, start hour, overrides, faults)
# faults: (day index, clock hour, type, duration [s], magnitude) - magnitude None = random
SHOWCASE = (
    ("room_20C", 0, 14.0, dict(sched=[(6.0, 21.0, 10), (8.5, 20.0, 15), (17.0, 21.5, 15), (22.5, 18.5, 15)],
                                duty=0.5, lag=60, noise=0.02),
     [(0, 19.5, "heat_event", 8 * MIN, 300.0), (1, 2.0, "setpoint_fault", 120 * MIN, 3.5),
      (1, 10.0, "door_open", 40 * MIN, 12.0), (2, 15.0, "control_fail", 150 * MIN, None),
      (2, 21.0, "spike", 2, 5.0)]),
    ("sauna_50C", 4, 11.0, dict(sched=[(9.0, 50.0, 10), (22.0, 44.0, 10)], duty=0.3, lag=60, noise=0.03),
     [(0, 15.0, "control_stuck", 70 * MIN, None), (1, 13.0, "control_fail", 120 * MIN, None),
      (1, 20.0, "noise", 25 * MIN, 1.0), (2, 10.5, "door_open", 30 * MIN, 10.0),
      (2, 17.0, "stuck", 40 * MIN, None)]),
    ("freezer_-18C", 3, 9.5, dict(sched=[(0.0, -18.0, 0)], defrost=(8.0, 2.0, 25 * MIN, 55.0), lag=60,
                                   noise=0.02, duty=0.5),
     [(0, 14.0, "door_open", 25 * MIN, 30.0), (1, 6.0, "control_fail", 120 * MIN, None),
      (2, 13.0, "offset", 60 * MIN, 4.0), (2, 20.5, "heat_event", 30 * MIN, 45.0)]),
)
SHOWCASE_DAYS = 3


def showcase() -> dict:
    rng = np.random.default_rng(20261012)
    prm, sec0, events = [], [], []
    for _, env, start_h, over, faults in SHOWCASE:
        p = sample_params(env, rng)
        p.update(over)
        s0 = int(start_h * HOUR)
        prm.append(p)
        sec0.append(s0)
        events.append(sorted(((typ, int(day * DAY + h * HOUR - s0), dur, mag)
                              for day, h, typ, dur, mag in faults), key=lambda e: e[1]))
    out = run(prm, sec0, SHOWCASE_DAYS, events, rng, keep_codes=True)
    out["names"] = np.array([s[0] for s in SHOWCASE])
    return out


def write_csv(path: Path, temp: np.ndarray, sec0: int, code: np.ndarray | None = None):
    """timestamp,temperature[,anomaly] - 1 Hz from the moment the sensor was installed."""
    t = np.datetime_as_string(BASE_DATE + np.timedelta64(int(sec0), "s") + np.arange(len(temp)), unit="s")
    ts = np.char.replace(t, "T", " ")
    vals = np.char.mod("%.2f", temp / 100)
    if code is None:
        rows = [f"{a},{b}" for a, b in zip(ts, vals)]
        head = "timestamp,temperature"
    else:
        names = np.array([""] + list(TYPES))[code]
        rows = [f"{a},{b},{c}" for a, b, c in zip(ts, vals, names)]
        head = "timestamp,temperature,anomaly"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(head + "\n" + "\n".join(rows) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--out", type=Path, default=Path("data") / "showcase")
    a = ap.parse_args()
    sc = showcase()
    for i, name in enumerate(sc["names"]):
        write_csv(a.out / f"{name}.csv", sc["temp"][i], int(sc["sec0"][i]), sc["code"][i])
        x = sc["temp"][i] / 100
        s0 = int(sc["sec0"][i])
        print(f"{name:13s} {len(x) // DAY} days from {s0 // HOUR:02d}:{s0 % HOUR // MIN:02d}"
              f"  min {x.min():7.2f}  max {x.max():7.2f}  anomalous windows {int(sc['label'][i].sum())}"
              f" -> {a.out / (name + '.csv')}")


if __name__ == "__main__":
    main()
