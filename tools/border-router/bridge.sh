#!/bin/bash
# Poll the Matter nodes from the controller and forward the state to the app
# API. Matter stops at the local network; this is the hop to the cloud.
#
#   ./bridge.sh [interval-seconds]
#
# Each cycle reads
#   sensor  node 1  endpoint 1  TemperatureMeasurement.MeasuredValue  (0.01 C)
#   judge   node 2  endpoint 2  OnOff.OnOff                           (alarm)
# and POSTs
#   {"temperature":2375,"alarm":true,"ts":"2026-10-11T12:34:56Z"}
# to $API_URL/matter/events. A failed POST is logged and retried next cycle.

set -uo pipefail
source "$(dirname "$0")/env.sh"

interval="${1:-2}"
endpoint="$API_URL/matter/events"

read_temperature() {
	ct temperaturemeasurement read measured-value "$SENSOR_NODE" "$SENSOR_TEMP_ENDPOINT" 2>/dev/null \
		| sed -n 's/.*MeasuredValue: *\(-\?[0-9]\+\|null\).*/\1/p' | head -1
}

read_alarm() {
	ct onoff read on-off "$JUDGE_NODE" "$JUDGE_ALARM_ENDPOINT" 2>/dev/null \
		| sed -n 's/.*OnOff: *\(TRUE\|FALSE\).*/\1/p' | head -1
}

last_payload=""

echo "bridge: posting to $endpoint every ${interval}s"
while true; do
	temp="$(read_temperature)"
	alarm="$(read_alarm)"

	[ -z "$temp" ] && temp=null
	case "$alarm" in
	TRUE) alarm=true ;;
	FALSE) alarm=false ;;
	*) alarm=null ;;
	esac

	ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
	payload="{\"temperature\":$temp,\"alarm\":$alarm,\"ts\":\"$ts\"}"

	if [ "$temp" = null ] && [ "$alarm" = null ]; then
		echo "$ts  both reads failed (nodes offline or not commissioned?)"
	else
		echo "$ts  temp=$temp alarm=$alarm"
		if ! curl -fsS -m 5 -X POST -H 'Content-Type: application/json' -d "$payload" "$endpoint" >/dev/null; then
			echo "$ts  POST failed"
		fi
	fi

	sleep "$interval"
done
