# Border router + Matter controller (Raspberry Pi)

The Pi does three jobs:

| Job | Software | Script |
|---|---|---|
| Thread border router | OTBR in Docker (`nrfconnect/otbr:fbde28a`, matches NCS v3.3.4) + nRF52840 Dongle running the `coprocessor` (RCP) sample | `otbr/`, `thread-up.sh` |
| Matter controller / commissioner | `chip-tool` (arm64 build from `nrfconnect/sdk-connectedhomeip` v3.3.0) — issues the fabric certificate (NOC) to each node, writes ACL and binding | `commission.sh` |
| Bridge to the app | polls the nodes with chip-tool and POSTs to the Axum API | `bridge.sh` |

Everything persists: once `commission.sh` has run, nodes stay on the fabric
across power cycles. Only a factory reset (or `--erase` flash) of a node, or
deleting `~/chip-tool-storage` on the Pi, requires commissioning again.

## Hardware

- Raspberry Pi 4 (any 64-bit Pi works), Raspberry Pi OS 64-bit, same Wi-Fi as the PC
- nRF52840 Dongle with RCP firmware:
  ```
  west build -b nrf52840dongle/nrf52840 -d C:\ncs\tmp\rcp C:\ncs\v3.3.4\nrf\samples\openthread\coprocessor
  nrfutil nrf5sdk-tools pkg generate --hw-version 52 --sd-req 0x00 --application C:\ncs\tmp\rcp\coprocessor\zephyr\zephyr.hex --application-version 1 C:\ncs\tmp\rcp\rcp_dongle.zip
  nrfutil nrf5sdk-tools dfu usb-serial -pkg C:\ncs\tmp\rcp\rcp_dongle.zip -p COMx   # dongle in bootloader mode
  ```
  It enumerates as `Thread Co-Processor`; `otbr/start.sh` finds it by that USB product string, so the sensor dongle and the DK are never picked by mistake.

## Setup

```
scp -r tools/border-router devfive@<pi-ip>:~/ansim
ssh devfive@<pi-ip>
cd ~/ansim && chmod +x *.sh otbr/*.sh && ./install.sh
# plug in the RCP dongle
sudo systemctl start otbr
./thread-up.sh            # creates the Thread network, prints the dataset
```

## Commissioning (controller hands out certificates)

Flash both nodes (see `firmware/matter/*/README.md`), power them, then:

```
./commission.sh            # BLE: nodes are factory-fresh and advertising
./commission.sh onnetwork  # nodes already on Thread (dataset set via shell)
./commission.sh ble link   # re-apply ACL + binding only
```

What it does, in order:

1. `pairing ble-thread 1 hex:<dataset> 20202021 3840` — sensor dongle becomes node 1
2. `pairing ble-thread 2 hex:<dataset> 20202021 3841` — judge DK becomes node 2
3. ACL on node 1: node 2 may *View* endpoint 1 / cluster 0x0402 (TemperatureMeasurement)
4. Binding on node 2 endpoint 1 → node 1 endpoint 1 cluster 0x0402
5. Reads back temperature, binding table and alarm state

Values (node IDs, discriminators, passcode, endpoints) live in `env.sh` and must
match the firmware Kconfig.

## Bridge

```
API_URL=http://<pc-ip>:8000 ./bridge.sh 2
```

POSTs `{"temperature":<0.01 C int|null>,"alarm":<bool|null>,"ts":"<iso8601>"}`
to `$API_URL/matter/events` every 2 s. The API route is not implemented yet;
`app/apis/api/src/routes/mod.rs` needs a handler for it.

## Debug

```
sudo docker exec otbr ot-ctl state          # leader / router = good
sudo docker exec otbr ot-ctl neighbor table # commissioned nodes show up here
chip-tool temperaturemeasurement read measured-value 1 1 --storage-directory ~/chip-tool-storage
chip-tool binding read binding 2 1 --storage-directory ~/chip-tool-storage
chip-tool onoff read on-off 2 2 --storage-directory ~/chip-tool-storage
sudo journalctl -u otbr -f
```

Notes:
- The host `avahi-daemon` is disabled by `install.sh`; the OTBR container runs
  its own mDNS on the host network and the two would collide on port 5353.
- `chip-tool` defaults to `/tmp` for its fabric storage, which is wiped on
  reboot; every script passes `--storage-directory ~/chip-tool-storage`.
