/*
 * Matter judge node on the nRF54LM20-DK.
 *
 * Based on nrf/samples/matter/light_switch (Nordic-5-Clause).
 */

#include "app_task.h"

#include <zephyr/logging/log.h>

LOG_MODULE_REGISTER(app, CONFIG_CHIP_APP_LOG_LEVEL);

int main()
{
	CHIP_ERROR err = AppTask::Instance().StartApp();

	LOG_ERR("Exited with code %" CHIP_ERROR_FORMAT, err.Format());
	return err == CHIP_NO_ERROR ? EXIT_SUCCESS : EXIT_FAILURE;
}
