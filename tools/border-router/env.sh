# Shared settings for the Raspberry Pi border router / Matter controller.
# Source this file; do not run it.

# Matter node IDs handed out by chip-tool at commissioning time.
SENSOR_NODE=1   # nRF52840 Dongle, firmware/matter/sensor_dongle
JUDGE_NODE=2    # nRF54LM20-DK,   firmware/matter/judge_dk

# chip-tool's own node ID on the fabric (chip-tool default).
CONTROLLER_NODE=112233
FABRIC_INDEX=1

# Commissioning values baked into the firmware (test values, not for products).
SENSOR_DISCRIMINATOR=3840   # 0xF00
JUDGE_DISCRIMINATOR=3841    # 0xF01
PASSCODE=20202021

# Endpoints and clusters.
SENSOR_TEMP_ENDPOINT=1
TEMPERATURE_MEASUREMENT_CLUSTER=1026   # 0x0402
JUDGE_BINDING_ENDPOINT=1
JUDGE_ALARM_ENDPOINT=2                 # OnOff server: true = alarm

# chip-tool keeps fabric credentials here. Default is /tmp, which is wiped on reboot.
CHIP_STORAGE="${CHIP_STORAGE:-$HOME/chip-tool-storage}"
CHIP_TOOL="${CHIP_TOOL:-chip-tool}"

# Where bridge.sh posts events. The PC running the Axum API, port from app/apis/api config.
API_URL="${API_URL:-http://192.168.0.10:8000}"

ct() {
	"$CHIP_TOOL" "$@" --storage-directory "$CHIP_STORAGE"
}

otctl() {
	sudo docker exec otbr ot-ctl "$@"
}
