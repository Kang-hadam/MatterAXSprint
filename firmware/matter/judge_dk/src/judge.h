/*
 * Reads the bound temperature sensor over Matter once per second, feeds the
 * readings into the on-device anomaly model (firmware/anomaly) and publishes
 * the model's verdict as the OnOff attribute of endpoint 2 (plus an LED).
 *
 * The model works on 60-sample windows: the first 5 windows recognise the
 * space (level, swing, noise), every later window is scored against what was
 * recognised (BASIC) or, once a time of day has been learned, against the
 * daily profile (FULL).
 */

#pragma once

#include "binding/binding_handler.h"

#include "anomaly.h"

#include <app/util/basic-types.h>
#include <lib/core/CHIPError.h>

#include <zephyr/kernel.h>

class Judge {
public:
	static constexpr chip::EndpointId kBindingEndpointId = 1;
	static constexpr chip::EndpointId kAlarmEndpointId = 2;

	static constexpr uint32_t kReadIntervalMs = 1000;
	/* No reading for this long: the sample stream is broken, so the detector
	 * state is dropped and recognition starts over with the next reading. */
	static constexpr uint32_t kSensorSilenceMs = 30000;
	/* Consecutive normal windows needed before an alarm is cleared. */
	static constexpr uint32_t kAlarmClearWindows = 1;

	static Judge &Instance()
	{
		static Judge sJudge;
		return sJudge;
	}

	void Init();

	/* Called with every reading that arrived from the sensor (Matter thread).
	 * Stores it; the model is fed from the 1 s timer (FeedSample). */
	void OnTemperature(int16_t centi);

	/* Called when a controller wrote OnOff on the alarm endpoint directly. */
	void OnAlarmAttributeWritten(bool on);

	bool HasReading() const { return mHaveReading; }
	int16_t LastTemperature() const { return mLastTemperature; }
	bool AlarmOn() const { return mAlarmOn; }

	uint8_t Phase() const { return mLastResult.phase; }
	float LastScore() const { return mLastResult.score; }
	float RecognisedLevel() const { return mState.L0; }
	uint32_t WindowsCompleted() const { return mState.k; }
	uint16_t SamplesInWindow() const { return mState.n; }

private:
	static void ReadTimerCallback(k_timer *timer);
	static void RequestRead();
	static void ReadBoundSensor(const chip::app::Clusters::Binding::TableEntry &binding,
				    chip::OperationalDeviceProxy *device,
				    Nrf::Matter::BindingHandler::BindingData &bindingData);

	void ResetDetector();
	void FeedSample(int64_t nowUptime);
	void OnWindow(const ad_result_t &result, int16_t centi);
	void SetAlarm(bool on);
	void SetAlarmLed(bool on);

	k_timer mReadTimer;
	ad_state_t mState;
	ad_result_t mLastResult = { 0.0f, AD_LEARNING, 0 };
	int64_t mLastReadingUptime = 0;
	int16_t mLastTemperature = 0;
	uint32_t mNormalStreak = 0;
	bool mHaveReading = false;
	bool mAlarmOn = false;
};
