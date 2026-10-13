# Matter temperature sensor — nRF52840 Dongle

Matter node 1 of the demo. Reads the temperature sensor inside the nRF52840
every second and publishes it as `TemperatureMeasurement.MeasuredValue`
(endpoint 1, cluster 0x0402, unit 0.01 °C). The judge board (node 2) reads it
through a Matter binding.

Based on `nrf/samples/matter/temperature_sensor` (NCS v3.3.4) with these
changes for the dongle:

| Area | Change | Why |
|---|---|---|
| Bootloader | none (`SB_CONFIG_BOOTLOADER_NONE`), no partition manager | The dongle boots through its factory Nordic USB bootloader at 0xE0000 |
| Flash layout | app 0x1000–0xD8000, settings 0xD8000–0xE0000 (overlay) + `CONFIG_USE_DT_CODE_PARTITION` | Keep the bootloader and its settings pages intact |
| Factory data | off; identity from `CONFIG_CHIP_DEVICE_*` test values | No factory data partition |
| OTA / NFC | off | No MCUboot; no NFC antenna |
| Console | USB CDC ACM (`Ansim Matter Temp Sensor`) | No UART-to-USB on the dongle |
| ICD | SIT, 1 s slow poll | USB powered; reads must be answered quickly |
| Temperature | nRF52840 die sensor (`temp` node, `SENSOR_CHAN_DIE_TEMP`) | Sample simulates a ramp |

## Build

Matter header paths exceed Windows' 260-character limit when the build
directory is long. Always build into a short path:

```
west build -b nrf52840dongle/nrf52840 -d C:\ncs\tmp\mts firmware/matter/sensor_dongle
```

## Flash (USB DFU)

1. Enter the bootloader: press the side RESET button (red LED pulses), or over
   the CDC shell: `gpio conf gpio@50000000 19 o0`.
2. Package and flash:

```
nrfutil nrf5sdk-tools pkg generate --hw-version 52 --sd-req 0x00 --application C:\ncs\tmp\mts\sensor_dongle\zephyr\zephyr.hex --application-version 1 C:\ncs\tmp\mts\sensor_dongle.zip
nrfutil nrf5sdk-tools dfu usb-serial -pkg C:\ncs\tmp\mts\sensor_dongle.zip -p COMx
```

## Commissioning values

| | |
|---|---|
| Discriminator | 3840 (0xF00) |
| Passcode | 20202021 |
| Vendor / Product ID | 0xFFF1 / 0x800D (test) |
| BLE name | `AnsimTemp` |

See `tools/border-router/commission.sh`.

## LEDs / button

Board module defaults (`DK_LIBRARY` with the dongle's `led0..led3`, `sw0`):
LED0 (green) shows Matter connectivity state; button short press = ICD
user-action trigger, long press = factory reset. Shell: `matter device factoryreset`.
