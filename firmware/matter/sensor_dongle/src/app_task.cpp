/*
 * Matter temperature sensor on the nRF52840 Dongle.
 *
 * Based on nrf/samples/matter/temperature_sensor (Nordic-5-Clause).
 * The simulated temperature ramp of the sample is replaced by the
 * temperature sensor inside the nRF52840 chip.
 */

#include "app_task.h"
#include "status_log.h"

#include "app/matter_init.h"
#include "app/task_executor.h"
#include "board/board.h"
#include "clusters/identify.h"
#include "lib/core/CHIPError.h"

#include <app-common/zap-generated/attributes/Accessors.h>

#include <zephyr/device.h>
#include <zephyr/drivers/sensor.h>
#include <zephyr/logging/log.h>

#include <cstdlib>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

using namespace ::chip;
using namespace ::chip::app;
using namespace ::chip::DeviceLayer;

namespace
{
constexpr chip::EndpointId kTemperatureSensorEndpointId = 1;

Nrf::Matter::IdentifyCluster sIdentifyCluster(kTemperatureSensorEndpointId);

const device *const sTempDev = DEVICE_DT_GET(DT_NODELABEL(temp));
} /* namespace */

/* The dongle has one button (sw0 = DK button 1). The board module's default
 * handler owns it for factory reset (long press); a short press is the ICD
 * user-action trigger that puts the device in active mode for a while. */
void AppTask::ButtonEventHandler(Nrf::ButtonState state, Nrf::ButtonMask hasChanged)
{
#ifdef CONFIG_CHIP_ICD_UAT_SUPPORT
	if (DK_BTN1_MSK & state & hasChanged) {
		LOG_INF("ICD UserActiveMode has been triggered.");
		Server::GetInstance().GetICDManager().OnNetworkActivity();
	}
#else
	ARG_UNUSED(state);
	ARG_UNUSED(hasChanged);
#endif
}

void AppTask::UpdateTemperatureMeasurement()
{
	sensor_value temperature;
	int result = sensor_sample_fetch(sTempDev);

	if (result != 0) {
		LOG_ERR("Fetching the die temperature failed with: %d", result);
		return;
	}

	result = sensor_channel_get(sTempDev, SENSOR_CHAN_DIE_TEMP, &temperature);
	if (result != 0) {
		LOG_ERR("Reading the die temperature failed with: %d", result);
		return;
	}

	/* val1 is the integer part, val2 the fraction in millionths.
	 * Cluster unit is 0.01 degC, so val2 / 10000. */
	int32_t centi = temperature.val1 * 100 + temperature.val2 / 10000;

	if (centi < mTemperatureSensorMinValue || centi > mTemperatureSensorMaxValue) {
		LOG_WRN("temp %d.%02d C outside the cluster range %d..%d", centi / 100, abs(centi % 100),
			mTemperatureSensorMinValue, mTemperatureSensorMaxValue);
		centi = centi < mTemperatureSensorMinValue ? mTemperatureSensorMinValue : mTemperatureSensorMaxValue;
	}

	mCurrentTemperature = static_cast<int16_t>(centi);
	LOG_INF("temp %d.%02d C", mCurrentTemperature / 100, abs(mCurrentTemperature % 100));
}

void AppTask::UpdateTemperatureTimeoutCallback(k_timer *timer)
{
	if (!timer || !timer->user_data) {
		return;
	}

	DeviceLayer::PlatformMgr().ScheduleWork(
		[](intptr_t p) {
			AppTask::Instance().UpdateTemperatureMeasurement();

			Protocols::InteractionModel::Status status =
				Clusters::TemperatureMeasurement::Attributes::MeasuredValue::Set(
					kTemperatureSensorEndpointId, AppTask::Instance().GetCurrentTemperature());

			if (status != Protocols::InteractionModel::Status::Success) {
				LOG_ERR("Updating temperature measurement failed %x", to_underlying(status));
			}
		},
		reinterpret_cast<intptr_t>(timer->user_data));
}

CHIP_ERROR AppTask::Init()
{
	/* Initialize Matter stack */
	ReturnErrorOnFailure(Nrf::Matter::PrepareServer());

	if (!Nrf::GetBoard().Init(ButtonEventHandler)) {
		LOG_ERR("User interface initialization failed.");
		return CHIP_ERROR_INCORRECT_STATE;
	}

	/* Register Matter event handler that controls the connectivity status LED based on the captured Matter network
	 * state. */
	ReturnErrorOnFailure(Nrf::Matter::RegisterEventHandler(Nrf::Board::DefaultMatterEventHandler, 0));
	ReturnErrorOnFailure(StatusLog::Init());

	if (!device_is_ready(sTempDev)) {
		LOG_ERR("Die temperature sensor not ready");
		return chip::System::MapErrorZephyr(-ENODEV);
	}

	ReturnErrorOnFailure(sIdentifyCluster.Init());

	ReturnErrorOnFailure(Nrf::Matter::StartServer());
	StatusLog::PrintCurrent();
	return CHIP_NO_ERROR;
}

CHIP_ERROR AppTask::StartApp()
{
	ReturnErrorOnFailure(Init());

	DataModel::Nullable<int16_t> val;
	Protocols::InteractionModel::Status status =
		Clusters::TemperatureMeasurement::Attributes::MinMeasuredValue::Get(kTemperatureSensorEndpointId, val);

	if (status != Protocols::InteractionModel::Status::Success || val.IsNull()) {
		LOG_ERR("Failed to get temperature measurement min value %x", to_underlying(status));
		return CHIP_ERROR_INCORRECT_STATE;
	}

	mTemperatureSensorMinValue = val.Value();

	status = Clusters::TemperatureMeasurement::Attributes::MaxMeasuredValue::Get(kTemperatureSensorEndpointId, val);

	if (status != Protocols::InteractionModel::Status::Success || val.IsNull()) {
		LOG_ERR("Failed to get temperature measurement max value %x", to_underlying(status));
		return CHIP_ERROR_INCORRECT_STATE;
	}

	mTemperatureSensorMaxValue = val.Value();

	k_timer_init(&mTimer, AppTask::UpdateTemperatureTimeoutCallback, nullptr);
	k_timer_user_data_set(&mTimer, this);
	k_timer_start(&mTimer, K_MSEC(kTemperatureMeasurementIntervalMs), K_MSEC(kTemperatureMeasurementIntervalMs));

	while (true) {
		Nrf::DispatchNextTask();
	}

	return CHIP_NO_ERROR;
}
