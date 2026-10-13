/*
 * Matter judge node on the nRF54LM20-DK.
 *
 * Based on nrf/samples/matter/light_switch (Nordic-5-Clause).
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

private:
	CHIP_ERROR Init();

	static void ButtonEventHandler(Nrf::ButtonState state, Nrf::ButtonMask hasChanged);
};
