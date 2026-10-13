# Matter judge node — nRF54LM20-DK

Matter node 2 of the demo. Every second it reads the temperature of the sensor
dongle (node 1) through a Matter **binding**, feeds the reading into the
on-device anomaly model (`firmware/anomaly`), and publishes the model's
verdict as `OnOff.OnOff` on endpoint 2 and on **LED2**. The controller
(chip-tool on the Raspberry Pi) reads that attribute and forwards it to the
app.

Based on `nrf/samples/matter/light_switch` (NCS v3.3.4): the binding
infrastructure is reused, the light-switch button/dimmer logic is replaced by
`src/judge.cpp`.

## Endpoints

| Endpoint | Device type | Clusters | Role |
|---|---|---|---|
| 0 | Root node | Basic Information, Operational Credentials, ... | commissioning |
| 1 | Dimmer switch (0x0104) | **Binding** server, TemperatureMeasurement / OnOff / LevelControl clients | the sensor is bound here |
| 2 | On/Off Light (0x0100) | **OnOff** server, Identify, Groups | `OnOff` = alarm |

## Verdict (anomaly model)

`src/judge.cpp` feeds every reading into `ad_feed()`; every 60 samples
`ad_run_inference()` returns `{score, phase, anomaly}`.

| Phase | When | Log |
|---|---|---|
| `LEARNING` | first 5 min | `(hh:mm:ss, 23.75 C, false) recognising 2/5 min` |
| `BASIC` | from minute 6, judged against the recognised level | `(..., 23.80 C, false) level 23.75 C score 0.8 [BASIC]` |
| `FULL` | time of day already learned (second day on) | `... [FULL]` |

Alarm ON the minute `score >= threshold` (`[model] ANOMALY score 12.3 ...`),
OFF after `kAlarmClearWindows` normal minutes. If no reading arrives for
`kSensorSilenceMs` (30 s) the detector state is dropped and the space is
recognised again. The per-second line is kept for the demo log; `[model]`
lines mark recognition, phase changes and alarm edges.

The DK has no wall clock: the daily profile runs on seconds since boot mod
24 h (periodic, offset from real time). Model details, retraining and
metrics: [`firmware/anomaly/README.md`](../../anomaly/README.md).

The previous rule (`baseline + 5.00 °C` → ON, `+ 4.50` → OFF, 1 s response)
lives on in `firmware/temp_alarm/led_dk`.

Known pitfalls, both hit while bringing the model up:

- `ReadBoundSensor` must not hand heap copies of `BindingData` to
  `BindingHandler::OnInvokeCommandSucces/Failure` — only the callback that
  fires frees its copy, the other leaks (~40 B per read) and the Matter heap
  runs out after ~5 min (`Read MeasuredValue request failed: b`, then
  `abort()` on the CHIP thread). The callbacks capture nothing.
- Do not set `CONFIG_FPU=y`: it switches on `FPU_SHARING`, which grows every
  thread's exception frame and overflows the stack-tuned Matter/Thread
  threads. The model runs in soft-float, once a minute.

## Data model changes (ZAP)

`src/default_zap/judge_dk.zap` is produced from the light_switch and
light_bulb sample ZAPs by `src/default_zap/make_judge_zap.py`; the generated
sources are checked in. After editing the script or the `.zap`:

```
python firmware/matter/judge_dk/src/default_zap/make_judge_zap.py C:/ncs/v3.3.4
west zap-generate -z firmware/matter/judge_dk/src/default_zap/judge_dk.zap
```

(`west zap-generate` installs the ZAP tool on first use.)

## Build / flash

```
west build -b nrf54lm20dk/nrf54lm20b/cpuapp -d C:\ncs\tmp\mjd firmware/matter/judge_dk
west flash -d C:\ncs\tmp\mjd
```

Short build directory is required: Matter header paths exceed Windows' path
limit otherwise. MCUboot and factory data are generated as in the sample.
`CMakeLists.txt` compiles `../../anomaly/src/anomaly.c` with
`-ffp-contract=off` so the scores stay bit-identical to the Python reference.

## Commissioning values

| | |
|---|---|
| Discriminator | 3841 (0xF01) |
| Passcode | 20202021 |
| Vendor / Product ID | 0xFFF1 / 0x8004 (test) |
| BLE name | `AnsimJudge` |

## After commissioning (controller side)

Node 1 = sensor, node 2 = this board, chip-tool = 112233, fabric 1.
`tools/border-router/commission.sh` runs these.

```
# sensor: let node 2 read TemperatureMeasurement on endpoint 1
chip-tool accesscontrol write acl '[{"fabricIndex":1,"privilege":5,"authMode":2,"subjects":[112233],"targets":null},{"fabricIndex":1,"privilege":1,"authMode":2,"subjects":[2],"targets":[{"cluster":1026,"endpoint":1,"deviceType":null}]}]' 1 0

# this node: bind endpoint 1 to the sensor's endpoint 1 / cluster 0x0402
chip-tool binding write binding '[{"fabricIndex":1,"node":1,"endpoint":1,"cluster":1026}]' 2 1

# alarm state
chip-tool onoff read on-off 2 2
```

## LEDs / buttons / shell

- LED1: Matter connectivity state (board module default)
- LED2: alarm
- Button 1: factory reset (long press), board module default
- Button 3: ICD user-active trigger
- Shell: `judge status` (temperature, phase, score, threshold, alarm), `judge table`, plus the standard `matter ...` commands
