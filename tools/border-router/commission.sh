#!/bin/bash
# Commission the two Matter nodes into this controller's fabric and wire them
# together. This is the step where the controller (chip-tool on the Pi) issues
# an operational certificate (NOC) to each node.
#
#   ./commission.sh [ble|onnetwork] [all|sensor|judge|link]
#
#   ble        (default) node is factory-fresh, advertising over BLE;
#              chip-tool sends it the Thread dataset and it joins the mesh.
#   onnetwork  node already joined the Thread network (dataset pre-provisioned
#              via the firmware shell); found over mDNS instead of BLE.
#   link       skip pairing, only (re)write the ACL on the sensor and the
#              binding on the judge.
#
# Results persist in $CHIP_STORAGE on the Pi and in each node's flash, so this
# runs once. Run again after a factory reset of a node.

set -euo pipefail
source "$(dirname "$0")/env.sh"

mode="${1:-ble}"
what="${2:-all}"

dataset_hex() {
	otctl dataset active -x | head -1 | tr -d '\r'
}

pair() {
	local node="$1" disc="$2" name="$3"
	echo "== pairing $name as node $node (discriminator $disc, $mode)"
	case "$mode" in
	ble)
		ct pairing ble-thread "$node" "hex:$(dataset_hex)" "$PASSCODE" "$disc"
		;;
	onnetwork)
		ct pairing onnetwork-long "$node" "$PASSCODE" "$disc"
		;;
	*)
		echo "unknown mode: $mode" >&2
		exit 2
		;;
	esac
}

# Let the judge (node 2) read the sensor's TemperatureMeasurement cluster.
# Entry 1 keeps the controller's admin access; entry 2 grants View to node 2
# on endpoint 1 / cluster 0x0402 only.
write_sensor_acl() {
	echo "== ACL on sensor: allow judge (node $JUDGE_NODE) to read temperature"
	ct accesscontrol write acl "[
		{\"fabricIndex\":$FABRIC_INDEX,\"privilege\":5,\"authMode\":2,\"subjects\":[$CONTROLLER_NODE],\"targets\":null},
		{\"fabricIndex\":$FABRIC_INDEX,\"privilege\":1,\"authMode\":2,\"subjects\":[$JUDGE_NODE],
		 \"targets\":[{\"cluster\":$TEMPERATURE_MEASUREMENT_CLUSTER,\"endpoint\":$SENSOR_TEMP_ENDPOINT,\"deviceType\":null}]}
	]" "$SENSOR_NODE" 0
}

# Tell the judge which node/endpoint/cluster it is bound to.
write_judge_binding() {
	echo "== binding on judge: sensor node $SENSOR_NODE endpoint $SENSOR_TEMP_ENDPOINT cluster $TEMPERATURE_MEASUREMENT_CLUSTER"
	ct binding write binding "[
		{\"fabricIndex\":$FABRIC_INDEX,\"node\":$SENSOR_NODE,\"endpoint\":$SENSOR_TEMP_ENDPOINT,\"cluster\":$TEMPERATURE_MEASUREMENT_CLUSTER}
	]" "$JUDGE_NODE" "$JUDGE_BINDING_ENDPOINT"
}

verify() {
	echo "== verify"
	ct temperaturemeasurement read measured-value "$SENSOR_NODE" "$SENSOR_TEMP_ENDPOINT" | grep -E 'MeasuredValue|Error' || true
	ct binding read binding "$JUDGE_NODE" "$JUDGE_BINDING_ENDPOINT" | grep -E 'Node|Error' || true
	ct onoff read on-off "$JUDGE_NODE" "$JUDGE_ALARM_ENDPOINT" | grep -E 'OnOff|Error' || true
}

case "$what" in
all)
	pair "$SENSOR_NODE" "$SENSOR_DISCRIMINATOR" sensor
	pair "$JUDGE_NODE" "$JUDGE_DISCRIMINATOR" judge
	write_sensor_acl
	write_judge_binding
	verify
	;;
sensor)
	pair "$SENSOR_NODE" "$SENSOR_DISCRIMINATOR" sensor
	;;
judge)
	pair "$JUDGE_NODE" "$JUDGE_DISCRIMINATOR" judge
	;;
link)
	write_sensor_acl
	write_judge_binding
	verify
	;;
*)
	echo "usage: $0 [ble|onnetwork] [all|sensor|judge|link]" >&2
	exit 2
	;;
esac
