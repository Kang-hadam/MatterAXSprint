/*
 * Temperature alarm LED on the nRF54LM20-DK.
 *
 * Receives temperature readings over Thread and turns LED0 on
 * when the temperature rises above the baseline.
 */

#include <stdlib.h>
#include <string.h>
#include <zephyr/kernel.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/openthread.h>
#include <openthread/message.h>
#include <openthread/udp.h>

#include "thread_net.h"

LOG_MODULE_REGISTER(temp_led, LOG_LEVEL_INF);

/*
 * Temperatures are in hundredths of a degree Celsius.
 * LED0 turns on at baseline + 5.00 C and turns off at baseline + 4.50 C.
 * The baseline is the first reading after this board or the sensor starts.
 */
#define ALARM_ON_DELTA  500
#define ALARM_OFF_DELTA 450

static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static otUdpSocket udp_socket;

static bool have_baseline;
static int32_t baseline;
static bool alarm_on;

static bool have_boot_id;
static uint32_t sensor_boot_id;

/* A new boot ID means that the sensor restarted: turn LED0 off and take a new baseline. */
static void on_boot_id(uint32_t boot_id)
{
	if (have_boot_id && boot_id == sensor_boot_id) {
		return;
	}

	sensor_boot_id = boot_id;
	have_boot_id = true;
	have_baseline = false;
	alarm_on = false;

	LOG_INF("sensor started, LED0 OFF, new baseline");
}

static void on_temp(int32_t centi)
{
	if (!have_baseline) {
		baseline = centi;
		have_baseline = true;
	}

	if (!alarm_on && centi >= baseline + ALARM_ON_DELTA) {
		alarm_on = true;
	} else if (alarm_on && centi <= baseline + ALARM_OFF_DELTA) {
		alarm_on = false;
	}

	gpio_pin_set_dt(&led, alarm_on);

	LOG_INF("temp %d.%02d C, baseline %d.%02d C, LED0 %s",
		centi / 100, centi % 100, baseline / 100, baseline % 100,
		alarm_on ? "ON" : "OFF");
}

/*
 * The sensor sends the reading and its boot ID as text,
 * for example "T=2375,B=12345" for 23.75 degrees.
 */
static void on_udp_receive(void *context, otMessage *msg, const otMessageInfo *info)
{
	char buf[32];
	char *end;
	uint16_t len;
	long centi;

	ARG_UNUSED(context);
	ARG_UNUSED(info);

	len = otMessageRead(msg, otMessageGetOffset(msg), buf, sizeof(buf) - 1);
	buf[len] = '\0';

	if (len < 3 || buf[0] != 'T' || buf[1] != '=') {
		return;
	}

	centi = strtol(&buf[2], &end, 10);
	if (end == &buf[2]) {
		return;
	}

	if (strncmp(end, ",B=", 3) == 0) {
		on_boot_id(strtoul(end + 3, NULL, 10));
	}

	on_temp((int32_t)centi);
}

int main(void)
{
	struct otInstance *ot = openthread_get_default_instance();
	otSockAddr addr = {.mPort = TEMP_UDP_PORT};
	otError err;
	int ret;

	if (!gpio_is_ready_dt(&led)) {
		LOG_ERR("LED0 is not ready");
		return 0;
	}

	ret = gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE);
	if (ret < 0) {
		LOG_ERR("Failed to configure LED0 [%d]", ret);
		return 0;
	}

	openthread_mutex_lock();
	err = otUdpOpen(ot, &udp_socket, on_udp_receive, NULL);
	if (err == OT_ERROR_NONE) {
		err = otUdpBind(ot, &udp_socket, &addr, OT_NETIF_THREAD);
	}
	openthread_mutex_unlock();
	if (err != OT_ERROR_NONE) {
		LOG_ERR("Failed to open the UDP socket [%d]", err);
		return 0;
	}

	ret = thread_net_start();
	if (ret < 0) {
		LOG_ERR("Failed to start Thread [%d]", ret);
	}

	return 0;
}
