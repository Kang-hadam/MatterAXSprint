/*
 * Temperature sensor on the nRF52840 Dongle.
 *
 * Reads the temperature sensor inside the nRF52840 chip once per second
 * and sends the value to all Thread nodes.
 *
 * The green LED blinks while the dongle looks for the Thread network
 * and stays on while the dongle is attached to the network.
 */

#include <stdio.h>
#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>
#include <zephyr/net/openthread.h>
#include <zephyr/random/random.h>
#include <openthread/ip6.h>
#include <openthread/message.h>
#include <openthread/thread.h>
#include <openthread/udp.h>

#include "thread_net.h"

LOG_MODULE_REGISTER(temp_sensor, LOG_LEVEL_INF);

#define SEND_PERIOD_MS  1000
#define BLINK_PERIOD_MS 250

static const struct device *const temp_dev = DEVICE_DT_GET(DT_NODELABEL(temp));
static const struct gpio_dt_spec led = GPIO_DT_SPEC_GET(DT_ALIAS(led0), gpios);

static otUdpSocket udp_socket;

/* Changes at each start. The LED board turns LED0 off when it sees a new value. */
static uint32_t boot_id;

static void on_blink_timer(struct k_timer *timer)
{
	ARG_UNUSED(timer);

	gpio_pin_toggle_dt(&led);
}

static K_TIMER_DEFINE(blink_timer, on_blink_timer, NULL);

/* Read the temperature in hundredths of a degree Celsius. */
static int read_temp(int32_t *centi)
{
	struct sensor_value val;
	int ret;

	ret = sensor_sample_fetch(temp_dev);
	if (ret < 0) {
		return ret;
	}

	ret = sensor_channel_get(temp_dev, SENSOR_CHAN_DIE_TEMP, &val);
	if (ret < 0) {
		return ret;
	}

	*centi = val.val1 * 100 + val.val2 / 10000;
	return 0;
}

static bool is_attached(struct otInstance *ot)
{
	switch (otThreadGetDeviceRole(ot)) {
	case OT_DEVICE_ROLE_CHILD:
	case OT_DEVICE_ROLE_ROUTER:
	case OT_DEVICE_ROLE_LEADER:
		return true;
	default:
		return false;
	}
}

/* Blink while not attached to the network. Stay on while attached. */
static void on_thread_state_changed(otChangedFlags flags, void *user_data)
{
	ARG_UNUSED(user_data);

	if (!(flags & OT_CHANGED_THREAD_ROLE)) {
		return;
	}

	if (is_attached(openthread_get_default_instance())) {
		k_timer_stop(&blink_timer);
		gpio_pin_set_dt(&led, 1);
	} else {
		k_timer_start(&blink_timer, K_MSEC(BLINK_PERIOD_MS), K_MSEC(BLINK_PERIOD_MS));
	}
}

static struct openthread_state_changed_callback ot_state_changed_cb = {
	.otCallback = on_thread_state_changed,
};

/*
 * Send the reading and the boot ID as text,
 * for example "T=2375,B=12345" for 23.75 degrees.
 */
static otError send_temp(int32_t centi)
{
	struct otInstance *ot = openthread_get_default_instance();
	otMessageInfo info = {0};
	otMessage *msg;
	otError err;
	char payload[32];
	int len;

	len = snprintf(payload, sizeof(payload), "T=%d,B=%u", centi, boot_id);

	openthread_mutex_lock();

	if (!is_attached(ot)) {
		err = OT_ERROR_INVALID_STATE;
		goto unlock;
	}

	msg = otUdpNewMessage(ot, NULL);
	if (msg == NULL) {
		err = OT_ERROR_NO_BUFS;
		goto unlock;
	}

	err = otMessageAppend(msg, payload, len);
	if (err == OT_ERROR_NONE) {
		otIp6AddressFromString(TEMP_UDP_GROUP, &info.mPeerAddr);
		info.mPeerPort = TEMP_UDP_PORT;
		err = otUdpSend(ot, &udp_socket, msg, &info);
	}

	if (err != OT_ERROR_NONE) {
		otMessageFree(msg);
	}

unlock:
	openthread_mutex_unlock();
	return err;
}

int main(void)
{
	int32_t centi;
	otError err;
	int ret;

	if (!device_is_ready(temp_dev)) {
		LOG_ERR("Temperature sensor is not ready");
		return 0;
	}

	if (!gpio_is_ready_dt(&led) || gpio_pin_configure_dt(&led, GPIO_OUTPUT_INACTIVE) < 0) {
		LOG_ERR("LED is not ready");
		return 0;
	}

	k_timer_start(&blink_timer, K_MSEC(BLINK_PERIOD_MS), K_MSEC(BLINK_PERIOD_MS));
	openthread_state_changed_callback_register(&ot_state_changed_cb);

	boot_id = sys_rand32_get();

	openthread_mutex_lock();
	err = otUdpOpen(openthread_get_default_instance(), &udp_socket, NULL, NULL);
	openthread_mutex_unlock();
	if (err != OT_ERROR_NONE) {
		LOG_ERR("Failed to open the UDP socket [%d]", err);
		return 0;
	}

	ret = thread_net_start();
	if (ret < 0) {
		LOG_ERR("Failed to start Thread [%d]", ret);
		return 0;
	}

	while (1) {
		ret = read_temp(&centi);
		if (ret < 0) {
			LOG_ERR("Failed to read the temperature [%d]", ret);
		} else {
			err = send_temp(centi);
			LOG_INF("temp %d.%02d C, %s", centi / 100, centi % 100,
				err == OT_ERROR_NONE ? "sent" : "not sent");
		}

		k_msleep(SEND_PERIOD_MS);
	}

	return 0;
}
