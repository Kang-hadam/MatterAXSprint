"""Check the C runtime against the Python reference and measure its Cortex-M33 footprint.

1. Parity   : host build (clang) of src/anomaly.c replays the embedded showcase deployments;
              every window's phase, alarm and score bits must equal ml/features.py (artifacts/showcase.npz)
2. Footprint: Cortex-M33 / FPv5 object (nRF54LM20 application core), -Os, as the firmware builds it:
              NVM = code + const data (weights), RAM = detector state (incl. daily profile) + peak stack
Usage: uv run python ml/c_check.py [--gcc path/to/arm-zephyr-eabi-gcc]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"                      # anomaly.c / anomaly.h / anomaly_model.h
TEST = ROOT / "selftest" / "src"        # test_data.c / test_data.h (showcase deployments)
ART = ROOT / "artifacts"
STRICT = ["-std=c11", "-ffp-contract=off", "-Wall", "-Wextra", "-Werror"]
M33 = ["-mcpu=cortex-m33", "-mthumb", "-mfloat-abi=hard", "-mfpu=fpv5-sp-d16", "-Os",
       "-ffunction-sections", "-fdata-sections", "-fstack-usage", *STRICT]
NEUTON = {         # nordicsemi.com/Products/Technologies/Edge-AI/Neuton-models (nRF52840, Neuton column)
    "A: bearing fault (Neuton)": dict(nvm_kb=6.6, ram_kb=1.2, inference_ms=1.46, accuracy=0.98),
    "B: magic wand (Neuton)": dict(nvm_kb=5.42, ram_kb=1.72, inference_ms=1.64, accuracy=0.94),
}


def sh(cmd: list[str]) -> str:
    return subprocess.run(cmd, check=True, capture_output=True, text=True).stdout


def parity(tmp: Path) -> dict:
    exe = tmp / "host_run.exe"
    sh(["clang", "-O2", *STRICT, "-D_CRT_SECURE_NO_WARNINGS", f"-I{SRC}", f"-I{TEST}",
        str(ROOT / "ml" / "host_run.c"), str(SRC / "anomaly.c"), str(TEST / "test_data.c"), "-o", str(exe)])
    lines = sh([str(exe)]).split("\n")
    state = int(lines[0].split()[1])
    rows = np.array([ln.split() for ln in lines[1:] if ln.strip()])
    sc, ph = rows[:, 0].astype(int), rows[:, 1].astype(np.uint8)
    bits, al = np.array([int(v, 16) for v in rows[:, 2]], np.uint32), rows[:, 3].astype(int).astype(bool)
    ref = np.load(ART / "showcase.npz")
    S, W = ref["score"].shape
    assert len(rows) == S * W and np.array_equal(sc, np.repeat(np.arange(S), W)), (len(rows), S * W)
    rbits = ref["score"].astype(np.float32).reshape(-1).view(np.uint32)
    return dict(windows=int(len(rows)), state_bytes=state,
                bit_exact_scores=int((bits == rbits).sum()),
                phase_matches=int((ph == ref["phase"].reshape(-1)).sum()),
                alarm_matches=int((al == ref["alarm"].reshape(-1)).sum()))


def sections(obj: Path, size_tool: str) -> dict:
    out = dict(text=0, rodata=0, data=0, bss=0)
    for line in sh([size_tool, "-A", str(obj)]).splitlines():
        p = line.split()
        if len(p) >= 2 and p[0].startswith(".") and p[1].isdigit():
            for k in out:
                if p[0] == f".{k}" or p[0].startswith(f".{k}."):
                    out[k] += int(p[1])
    return out


def stack(su: Path) -> dict:
    frames = {}
    for line in su.read_text().splitlines():
        m = re.match(r".*:(\w+)\s+(\d+)\s+(\S+)", line)
        if m:
            frames[m.group(1)] = int(m.group(2))
    api = ("ad_feed", "ad_run_inference", "ad_init")
    helpers = sum(v for k, v in frames.items() if k not in api)   # ponytail: upper bound, helpers may nest
    return dict(frames=frames, peak=max(frames.get("ad_feed", 0), frames.get("ad_run_inference", 0) + helpers))


def footprint(tmp: Path, cc: str, size_tool: str, nm_tool: str, extra: list[str], state: int) -> dict:
    obj = tmp / f"anomaly_{Path(cc).stem}.o"
    sh([cc, *extra, *M33, f"-I{SRC}", "-c", str(SRC / "anomaly.c"), "-o", str(obj)])
    sec = sections(obj, size_tool)
    su = obj.with_suffix(".su") if obj.with_suffix(".su").exists() else tmp / "anomaly.su"
    st = stack(su)
    undef = sorted(set(sh([nm_tool, "-u", str(obj)]).split()) - {"U"})
    nvm = sec["text"] + sec["rodata"] + sec["data"]
    return dict(compiler=Path(cc).name, sections=sec, stack=st, undefined_symbols=undef, nvm_bytes=nvm,
                ram_bytes=sec["data"] + sec["bss"] + state + st["peak"], state_bytes=state)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sdk_gcc = Path.home() / "zws/sdk/zephyr-sdk-1.0.1/gnu/arm-zephyr-eabi/bin/arm-zephyr-eabi-gcc.exe"
    ap.add_argument("--gcc", type=Path, default=sdk_gcc if sdk_gcc.exists() else None)
    a = ap.parse_args()
    report = json.loads((ART / "report.json").read_text(encoding="utf-8"))
    res = {}
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        res["parity"] = p = parity(tmp)
        if a.gcc:
            b = a.gcc.parent
            res["gcc"] = footprint(tmp, str(a.gcc), str(b / "arm-zephyr-eabi-size.exe"),
                                   str(b / "arm-zephyr-eabi-nm.exe"), [], p["state_bytes"])
        res["clang"] = footprint(tmp, "clang", shutil.which("llvm-size") or "llvm-size",
                                 shutil.which("llvm-nm") or "llvm-nm", ["--target=arm-none-eabi", "-ffreestanding"],
                                 p["state_bytes"])
    (ART / "footprint.json").write_text(json.dumps(res, indent=2), encoding="utf-8")

    print(f"parity (host C vs Python, {p['windows']} windows of 3 deployments): bit-exact scores "
          f"{p['bit_exact_scores']}/{p['windows']}, phases {p['phase_matches']}/{p['windows']}, "
          f"alarms {p['alarm_matches']}/{p['windows']}")
    for k in ("gcc", "clang"):
        if k in res:
            f = res[k]
            print(f"{f['compiler']:24s} text={f['sections']['text']} rodata={f['sections']['rodata']} "
                  f"data={f['sections']['data']} bss={f['sections']['bss']} state={f['state_bytes']} "
                  f"stack peak={f['stack']['peak']} B  undefined={f['undefined_symbols'] or 'none'}")
    best = res.get("gcc", res["clang"])
    t = report["test"]
    print(f"\n{'':30s}{'NVM KB':>8s}{'RAM KB':>8s}{'infer ms':>10s}{'accuracy':>10s}")
    for name, n in NEUTON.items():
        print(f"{name:30s}{n['nvm_kb']:8.2f}{n['ram_kb']:8.2f}{n['inference_ms']:10.2f}{n['accuracy']:10.3f}")
    print(f"{'this model (' + best['compiler'][:14] + ')':30s}{best['nvm_bytes'] / 1024:8.2f}"
          f"{best['ram_bytes'] / 1024:8.2f}{'(board)':>10s}{t['accuracy']:10.3f}"
          "   <- inference time: run the firmware on the nRF54LM20-DK")


if __name__ == "__main__":
    main()
