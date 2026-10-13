#!/bin/bash
# Bring up the Thread network on the border router and print the active
# dataset. Creates a new network only if the RCP has none stored.

set -euo pipefail
source "$(dirname "$0")/env.sh"

if ! sudo docker ps --format '{{.Names}}' | grep -qx otbr; then
	echo "otbr container is not running. Plug in the RCP dongle and: sudo systemctl start otbr" >&2
	exit 1
fi

state="$(otctl state | head -1 | tr -d '\r')"
echo "Thread state: $state"

if [ "$state" = "disabled" ] || [ "$state" = "detached" ]; then
	if otctl dataset active 2>&1 | grep -q 'Error'; then
		echo "No dataset stored, creating a new Thread network"
		otctl dataset init new >/dev/null
		otctl dataset networkname AnsimLoop >/dev/null
		otctl dataset channel 15 >/dev/null
		otctl dataset commit active >/dev/null
	fi
	otctl ifconfig up >/dev/null
	otctl thread start >/dev/null

	for _ in $(seq 1 30); do
		sleep 1
		state="$(otctl state | head -1 | tr -d '\r')"
		[ "$state" = "leader" ] || [ "$state" = "router" ] && break
	done
	echo "Thread state: $state"
fi

echo
echo "Active dataset (hex) - commission.sh reads this itself:"
otctl dataset active -x | head -1 | tr -d '\r'
