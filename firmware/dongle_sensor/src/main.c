/*
 * Sensor report for the nRF52840 Dongle.
 *
 * 1. Looks for external temperature/humidity sensors on all external pins.
 * 2. Prints the temperature of the sensor inside the chip once per second.
 *
 * The output goes to the USB serial port of the dongle.
 */

#include <zephyr/kernel.h>
#include <zephyr/device.h>
#include <zephyr/drivers/gpio.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/drivers/uart.h>
#include <zephyr/sys/printk.h>

#define PRINT_PERIOD_MS    1000
#define SUMMARY_EVERY      20
#define I2C_HALF_PERIOD_US 5
#define I2C_ADDR_FIRST     0x08
#define I2C_ADDR_LAST      0x77

struct ext_pin {
	const struct device *port;
	gpio_pin_t pin;
	const char *name;
};

#define P0 DEVICE_DT_GET(DT_NODELABEL(gpio0))
#define P1 DEVICE_DT_GET(DT_NODELABEL(gpio1))

/*
 * External pins of the dongle. Pins that the board uses itself
 * (LEDs, button, reset, crystal) are not in this list.
 */
static const struct ext_pin pins[] = {
	{P0, 13, "P0.13"}, {P0, 15, "P0.15"}, {P0, 17, "P0.17"}, {P0, 20, "P0.20"},
	{P0, 22, "P0.22"}, {P0, 24, "P0.24"}, {P1, 0, "P1.00"},  {P0, 9, "P0.09"},
	{P0, 10, "P0.10"}, {P0, 31, "P0.31"}, {P0, 29, "P0.29"}, {P0, 2, "P0.02"},
	{P1, 15, "P1.15"}, {P1, 13, "P1.13"}, {P1, 10, "P1.10"}, {P0, 4, "P0.04"},
	{P0, 11, "P0.11"}, {P0, 14, "P0.14"}, {P0, 26, "P0.26"}, {P1, 1, "P1.01"},
	{P1, 2, "P1.02"},  {P1, 4, "P1.04"},  {P1, 7, "P1.07"},  {P1, 11, "P1.11"},
};

static const struct device *const temp_dev = DEVICE_DT_GET(DT_NODELABEL(temp));
static const struct device *const console_dev = DEVICE_DT_GET(DT_CHOSEN(zephyr_console));

static int i2c_found;
static int dht_found;

/* Open-drain line control: release the line (pull-up) or drive it low. */
static void line_release(const struct ext_pin *p)
{
	gpio_pin_configure(p->port, p->pin, GPIO_INPUT | GPIO_PULL_UP);
}

static void line_low(const struct ext_pin *p)
{
	gpio_pin_configure(p->port, p->pin, GPIO_OUTPUT_LOW);
}

static int line_read(const struct ext_pin *p)
{
	return gpio_pin_get_raw(p->port, p->pin);
}

/* Send an I2C address and report if a device acknowledges it. */
static bool i2c_probe(const struct ext_pin *sda, const struct ext_pin *scl, uint8_t addr)
{
	uint8_t byte = addr << 1;
	bool ack;

	/* START */
	line_release(sda);
	line_release(scl);
	k_busy_wait(I2C_HALF_PERIOD_US);
	line_low(sda);
	k_busy_wait(I2C_HALF_PERIOD_US);
	line_low(scl);

	for (int bit = 7; bit >= 0; bit--) {
		if (byte & BIT(bit)) {
			line_release(sda);
		} else {
			line_low(sda);
		}
		k_busy_wait(I2C_HALF_PERIOD_US);
		line_release(scl);
		k_busy_wait(I2C_HALF_PERIOD_US);
		line_low(scl);
	}

	/* ACK bit: a device pulls SDA low. */
	line_release(sda);
	k_busy_wait(I2C_HALF_PERIOD_US);
	line_release(scl);
	k_busy_wait(I2C_HALF_PERIOD_US);
	ack = (line_read(sda) == 0);
	line_low(scl);

	/* STOP */
	line_low(sda);
	k_busy_wait(I2C_HALF_PERIOD_US);
	line_release(scl);
	k_busy_wait(I2C_HALF_PERIOD_US);
	line_release(sda);
	k_busy_wait(I2C_HALF_PERIOD_US);

	return ack;
}

/* Covers I2C sensors such as SHT3x/SHT4x, HTS221, HDC1080, Si7021, AHT20, BME280. */
static void scan_i2c(void)
{
	printk("I2C scan: %d x %d pin pairs, addresses 0x%02x to 0x%02x\n",
	       (int)ARRAY_SIZE(pins), (int)ARRAY_SIZE(pins) - 1, I2C_ADDR_FIRST, I2C_ADDR_LAST);

	for (size_t d = 0; d < ARRAY_SIZE(pins); d++) {
		for (size_t c = 0; c < ARRAY_SIZE(pins); c++) {
			if (c == d) {
				continue;
			}

			for (uint8_t addr = I2C_ADDR_FIRST; addr <= I2C_ADDR_LAST; addr++) {
				if (i2c_probe(&pins[d], &pins[c], addr)) {
					printk("  FOUND: I2C device 0x%02x (SDA %s, SCL %s)\n",
					       addr, pins[d].name, pins[c].name);
					i2c_found++;
				}
			}
		}

		gpio_pin_configure(pins[d].port, pins[d].pin, GPIO_DISCONNECTED);
		printk("  SDA %s done (%d of %d)\n", pins[d].name, (int)d + 1,
		       (int)ARRAY_SIZE(pins));
	}
}

/* A DHT11/DHT22 answers a 20 ms start pulse by pulling the line low. */
static void scan_dht(void)
{
	printk("DHT11/DHT22 scan: %d pins\n", (int)ARRAY_SIZE(pins));

	for (size_t i = 0; i < ARRAY_SIZE(pins); i++) {
		bool answered = false;

		line_low(&pins[i]);
		k_msleep(20);
		line_release(&pins[i]);

		for (int n = 0; n < 40 && !answered; n++) {
			k_busy_wait(5);
			answered = (line_read(&pins[i]) == 0);
		}

		if (answered) {
			printk("  FOUND: DHT sensor on %s\n", pins[i].name);
			dht_found++;
		}

		gpio_pin_configure(pins[i].port, pins[i].pin, GPIO_DISCONNECTED);
	}
}

static void print_summary(void)
{
	printk("--- external sensors found: I2C %d, DHT %d | chip: temperature sensor only ---\n",
	       i2c_found, dht_found);
}

static void wait_for_terminal(void)
{
	uint32_t dtr = 0;

	while (!dtr) {
		uart_line_ctrl_get(console_dev, UART_LINE_CTRL_DTR, &dtr);
		k_msleep(100);
	}
}

int main(void)
{
	struct sensor_value val;
	uint32_t count = 0;

	wait_for_terminal();

	printk("\nnRF52840 Dongle sensor report\n");

	if (!device_is_ready(temp_dev)) {
		printk("Chip temperature sensor is not ready\n");
		return 0;
	}

	scan_i2c();
	scan_dht();

	while (1) {
		if (count % SUMMARY_EVERY == 0) {
			print_summary();
		}

		if (sensor_sample_fetch(temp_dev) == 0 &&
		    sensor_channel_get(temp_dev, SENSOR_CHAN_DIE_TEMP, &val) == 0) {
			printk("[%5u s] chip temperature: %d.%02d C | humidity: %s\n",
			       k_uptime_get_32() / 1000, val.val1, val.val2 / 10000,
			       (i2c_found + dht_found) ? "external sensor found, see above"
						       : "no sensor");
		} else {
			printk("[%5u s] chip temperature: read error\n",
			       k_uptime_get_32() / 1000);
		}

		count++;
		k_msleep(PRINT_PERIOD_MS);
	}

	return 0;
}
