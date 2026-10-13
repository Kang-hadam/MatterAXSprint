"""
Build judge_dk.zap from the NCS light_switch and light_bulb sample ZAP files.

  python make_judge_zap.py C:/ncs/v3.3.4

Result:
  endpoint 0  as light_switch (root node, OTA requestor, ICD management)
  endpoint 1  as light_switch (Binding server, OnOff/LevelControl/Identify clients)
              + TemperatureMeasurement client  -> the sensor dongle is bound here
  endpoint 2  On/Off Light: OnOff server (+ Identify, Groups, Descriptor)
              -> OnOff = alarm state, written by the firmware, read by chip-tool

After changing this file run the script, then regenerate the code:

  west zap-generate -z firmware/matter/judge_dk/src/default_zap/judge_dk.zap
"""

import copy
import json
import os
import sys
from pathlib import Path

ncs = Path(sys.argv[1] if len(sys.argv) > 1 else "C:/ncs/v3.3.4")
samples = ncs / "nrf/samples/matter"
out = Path(__file__).with_name("judge_dk.zap")

switch = json.loads((samples / "light_switch/src/default_zap/light_switch.zap").read_text())
bulb = json.loads((samples / "light_bulb/src/default_zap/light_bulb.zap").read_text())

# --- endpoint 1: add the TemperatureMeasurement client -----------------------
ep1 = switch["endpointTypes"][1]
assert ep1["deviceTypeCode"] == 260, "expected the light switch endpoint"

ep1["clusters"].append(
    {
        "name": "Temperature Measurement",
        "code": 1026,
        "mfgCode": None,
        "define": "TEMPERATURE_MEASUREMENT_CLUSTER",
        "side": "client",
        "enabled": 1,
    }
)

# --- endpoint 2: On/Off Light built from the light bulb endpoint ------------
ep2 = copy.deepcopy(bulb["endpointTypes"][1])
assert ep2["deviceTypeCode"] == 257, "expected the dimmable light endpoint"

ep2["clusters"] = [c for c in ep2["clusters"] if c["code"] != 8]  # drop Level Control

onoff_light = {
    "code": 256,
    "profileId": 259,
    "label": "MA-onofflight",
    "name": "MA-onofflight",
    "deviceTypeOrder": 0,
}
ep2["id"] = 3
ep2["name"] = "MA-onofflight"
ep2["deviceTypeRef"] = onoff_light
ep2["deviceTypes"] = [onoff_light]
ep2["deviceIdentifiers"] = [256]
ep2["deviceTypeName"] = "MA-onofflight"
ep2["deviceTypeCode"] = 256

# --- ZCL/template package paths: the samples point 6 levels up to the NCS
# tree; this file lives in another repo, so re-point them at the given NCS.
for pkg in switch["package"]:
    if pkg.get("pathRelativity") == "relativeToZap":
        target = (samples / "light_switch/src/default_zap" / pkg["path"]).resolve()
        pkg["path"] = Path(os.path.relpath(target, out.parent)).as_posix()

switch["endpointTypes"].append(ep2)
switch["endpoints"].append(
    {
        "endpointTypeName": "MA-onofflight",
        "endpointTypeIndex": 2,
        "profileId": 259,
        "endpointId": 2,
        "networkId": 0,
        "parentEndpointIdentifier": None,
    }
)

out.write_text(json.dumps(switch, indent=2) + "\n")
print(f"wrote {out}")
for i, et in enumerate(switch["endpointTypes"]):
    print(f"endpoint type {i}: {et['name']}")
    for c in et["clusters"]:
        if c["code"] in (6, 30, 1026):
            print(f"    {c['code']:5} {c['name']:<25} {c['side']}")
