/*
 * Matter temperature sensor on the nRF52840 Dongle.
 *
 * Based on nrf/samples/matter/temperature_sensor (Nordic-5-Clause).
 */

#pragma once

#include "board/board.h"

#include <platform/CHIPDeviceLayer.h>

class AppTask {
public:
	static AppTask &Instance()
	{
		static AppTask sAppTask;
		return sAppTask;
	};

	CHIP_ERROR StartApp();

	/* Reads the chip die temperature into mCurrentTemperature.
	 * Unit is the cluster's: 100 x degrees Celsius (0.01 degC resolution). */
	void UpdateTemperatureMeasurement();

	int16_t GetCurrentTemperature() const { return mCurrentTemperature; }

private:
	CHIP_ERROR Init();
	k_timer mTimer;

	static constexpr uint16_t kTemperatureMeasurementIntervalMs = 1000;

	static void UpdateTemperatureTimeoutCallback(k_timer *timer);

	static void ButtonEventHandler(Nrf::ButtonState state, Nrf::ButtonMask hasChanged);

	int16_t mTemperatureSensorMaxValue = 0;
	int16_t mTemperatureSensorMinValue = 0;
	int16_t mCurrentTemperature = 0;
};
