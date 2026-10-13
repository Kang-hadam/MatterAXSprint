#!/bin/bash
# Start the OpenThread Border Router container against the RCP dongle.
# The RCP is found by its USB product string, so the DK (SEGGER) and the
# sensor dongle (Thread Temp Sensor) are never picked by mistake.
#
# Image: the official openthread/border-router. Nordic's nrfconnect/otbr
# (2024) does not understand the Spinel version of an NCS 3.3.4 RCP.

set -e

IMAGE="${OTBR_IMAGE:-openthread/border-router:latest}"
BACKBONE_IF="${BACKBONE_IF:-wlan0}"
DATA_DIR="${DATA_DIR:-$HOME/otbr/data}"

find_rcp() {
	local dev
	for dev in /dev/serial/by-id/*Thread_Co-Processor*; do
		[ -e "$dev" ] && readlink -f "$dev" && return 0
	done
	return 1
}

RCP_DEV="${RCP_DEV:-$(find_rcp || true)}"
if [ -z "$RCP_DEV" ]; then
	echo "RCP dongle (Thread Co-Processor) not found under /dev/serial/by-id" >&2
	ls -l /dev/serial/by-id 2>/dev/null >&2 || true
	exit 1
fi
echo "Using RCP at $RCP_DEV, backbone $BACKBONE_IF"

docker rm -f otbr >/dev/null 2>&1 || true
mkdir -p "$DATA_DIR"

# With --network host the container shares the host's stack, so the
# forwarding settings must be made on the host (docker refuses --sysctl here).
sysctl -qw net.ipv6.conf.all.disable_ipv6=0 net.ipv4.conf.all.forwarding=1 \
	net.ipv6.conf.all.forwarding=1 net.ipv6.conf.all.accept_ra=2 "net.ipv6.conf.$BACKBONE_IF.accept_ra=2"

exec docker run --rm --name otbr \
	--privileged \
	--network host \
	--volume "$RCP_DEV:/dev/radio" \
	--volume "$DATA_DIR:/data" \
	-e OT_RCP_DEVICE="spinel+hdlc+uart:///dev/radio?uart-baudrate=1000000" \
	-e OT_INFRA_IF="$BACKBONE_IF" \
	-e OT_LOG_LEVEL=5 \
	"$IMAGE"
