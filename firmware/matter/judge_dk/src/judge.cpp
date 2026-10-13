/*
 * Reads the bound temperature sensor over Matter once per second, feeds the
 * on-device anomaly model (firmware/anomaly/src) and publishes its verdict as
 * the OnOff attribute of endpoint 2 (plus LED2 on the DK).
 */

#include "judge.h"

#include "app/task_executor.h"
#include "board/board.h"

#include <app-common/zap-generated/attributes/Accessors.h>
#include <app-common/zap-generated/ids/Clusters.h>
#include <app/clusters/bindings/binding-table.h>
#include <app/server/Server.h>
#include <controller/ReadInteraction.h>
#include <platform/CHIPDeviceLayer.h>

#include <zephyr/logging/log.h>

#include <cstdlib>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

using namespace chip;
using namespace chip::app;
using namespace chip::app::Clusters;

namespace
{
constexpr uint32_t kReadStaleMs = 5000;
constexpr uint32_t kDaySeconds = 86400;
constexpr Nrf::DeviceLeds kAlarmLed = Nrf::DeviceLeds::LED2;

int64_t sReadRequestedUptime = 0;
bool sReadInFlight = false;
bool sSensorReachable = false;

void MarkReadDone()
{
	sReadInFlight = false;
}

void SetSensorReachable(bool reachable)
{
	if (reachable == sSensorReachable) {
		return;
	}
	sSensorReachable = reachable;
	if (reachable) {
		LOG_INF("[status] sensor connected over Thread, reading temperature every %u s", Judge::kReadIntervalMs / 1000);
	} else {
		LOG_WRN("[status] sensor not reachable");
	}
}

const char *PhaseName(uint8_t phase)
{
	switch (phase) {
	case AD_BASIC:
		return "BASIC";
	case AD_FULL:
		return "FULL";
	default:
		return "LEARNING";
	}
}

/* Scores are printed as tenths so the log needs no float printf support. */
int32_t Tenths(float value)
{
	return static_cast<int32_t>(value * 10.0f + (value >= 0.0f ? 0.5f : -0.5f));
}

int32_t Centi(float degc)
{
	return static_cast<int32_t>(degc * 100.0f + (degc >= 0.0f ? 0.5f : -0.5f));
}
} /* namespace */

void Judge::Init()
{
	Nrf::Matter::BindingHandler::Init();

	ad_init(&mState);
	SetAlarmLed(false);
	DeviceLayer::PlatformMgr().ScheduleWork(
		[](intptr_t) {
			OnOff::Attributes::OnOff::Set(kAlarmEndpointId, false);
		},
		0);

	LOG_INF("[model] anomaly detector loaded: thresholds BASIC %d.%d / FULL %d.%d, recognition %u min, state %u B",
		Tenths(ad_thr_basic) / 10, Tenths(ad_thr_basic) % 10, Tenths(ad_thr_full) / 10, Tenths(ad_thr_full) % 10,
		AD_RECOG, static_cast<unsigned int>(sizeof(mState)));

	k_timer_init(&mReadTimer, ReadTimerCallback, nullptr);
	k_timer_start(&mReadTimer, K_MSEC(kReadIntervalMs), K_MSEC(kReadIntervalMs));
}

void Judge::ReadTimerCallback(k_timer *timer)
{
	ARG_UNUSED(timer);
	Nrf::PostTask([] { RequestRead(); });
}

/* Runs on the Matter thread once per second: feeds the model, then issues one
 * read of the sensor through every unicast binding entry for the
 * TemperatureMeasurement cluster. */
void Judge::RequestRead()
{
	DeviceLayer::PlatformMgr().ScheduleWork(
		[](intptr_t) {
			Judge &judge = Instance();
			int64_t now = k_uptime_get();

			if (judge.mHaveReading && now - judge.mLastReadingUptime > kSensorSilenceMs) {
				judge.ResetDetector();
			}
			if (judge.mHaveReading) {
				judge.FeedSample(now);
			}

			if (sReadInFlight && now - sReadRequestedUptime < kReadStaleMs) {
				return;
			}

			if (Binding::Table::GetInstance().Size() == 0) {
				static bool sSaid = false;
				if (!sSaid) {
					LOG_INF("[status] no sensor bound yet, waiting for the controller to write the binding");
					sSaid = true;
				}
				return;
			}

			auto *data = Platform::New<Nrf::Matter::BindingHandler::BindingData>();
			VerifyOrReturn(data != nullptr, LOG_ERR("Out of memory for binding data"));

			data->EndpointId = kBindingEndpointId;
			data->ClusterId = TemperatureMeasurement::Id;
			data->CommandId = 0;
			data->InvokeCommandFunc = ReadBoundSensor;
			data->IsGroup.SetValue(false);

			sReadInFlight = true;
			sReadRequestedUptime = now;

			CHIP_ERROR err = Binding::Manager::GetInstance().NotifyBoundClusterChanged(
				data->EndpointId, data->ClusterId, static_cast<void *>(data));
			if (err != CHIP_NO_ERROR) {
				LOG_ERR("NotifyBoundClusterChanged failed: %" CHIP_ERROR_FORMAT, err.Format());
				MarkReadDone();
			}
		},
		0);
}

void Judge::ReadBoundSensor(const Binding::TableEntry &binding, OperationalDeviceProxy *device,
			    Nrf::Matter::BindingHandler::BindingData &bindingData)
{
	if (binding.type != Binding::MATTER_UNICAST_BINDING || device == nullptr) {
		LOG_WRN("Only unicast bindings are supported for the sensor");
		MarkReadDone();
		return;
	}

	VerifyOrDie(device->ConnectionReady());
	ARG_UNUSED(bindingData);

	using MeasuredValue = TemperatureMeasurement::Attributes::MeasuredValue::TypeInfo;

	/* The callbacks capture nothing on purpose. The binding handler's
	 * OnInvokeCommandSucces/Failure helpers each want their own heap copy of
	 * bindingData, but only the callback that fires frees its copy: one copy
	 * leaked per read and exhausted the Matter heap after ~5 minutes. The 1 s
	 * timer already retries, so no CASE recovery is needed here either. */
	auto onSuccess = [](const ConcreteDataAttributePath &path, const MeasuredValue::DecodableType &value) {
		MarkReadDone();
		SetSensorReachable(true);
		if (value.IsNull()) {
			LOG_WRN("Sensor reported a null temperature");
		} else {
			Instance().OnTemperature(value.Value());
		}
	};

	auto onFailure = [](const ConcreteDataAttributePath *path, CHIP_ERROR error) {
		MarkReadDone();
		SetSensorReachable(false);
		LOG_WRN("Reading the sensor failed: %" CHIP_ERROR_FORMAT, error.Format());
	};

	CHIP_ERROR err = Controller::ReadAttribute<MeasuredValue>(device->GetExchangeManager(),
								  device->GetSecureSession().Value(), binding.remote,
								  onSuccess, onFailure);

	if (err != CHIP_NO_ERROR) {
		LOG_ERR("Read MeasuredValue request failed: %" CHIP_ERROR_FORMAT, err.Format());
		MarkReadDone();
	}
}

void Judge::ResetDetector()
{
	LOG_WRN("[status] no reading for %u s, detector reset: recognising the space again (%u min)",
		kSensorSilenceMs / 1000, AD_RECOG);
	ad_init(&mState);
	mLastResult = { 0.0f, AD_LEARNING, 0 };
	mNormalStreak = 0;
	mHaveReading = false;
	if (mAlarmOn) {
		SetAlarm(false);
	}
}

void Judge::OnTemperature(int16_t centi)
{
	mLastReadingUptime = k_uptime_get();
	mLastTemperature = centi;
	mHaveReading = true;
}

/* Matter thread, driven by the 1 s timer rather than by arriving readings: a
 * Matter read over Thread often takes longer than a second, so the latest
 * reading is held and fed once per second to keep a 60-sample window at 60 s.
 * The DK has no wall clock, so the daily profile runs on seconds since boot
 * modulo one day: slot boundaries are offset from real time but 24 h periodic. */
void Judge::FeedSample(int64_t nowUptime)
{
	const int16_t centi = mLastTemperature;
	const uint32_t seconds = static_cast<uint32_t>(nowUptime / 1000);
	const uint32_t secOfDay = seconds % kDaySeconds;

	if (ad_feed(&mState, secOfDay, centi / 100.0f)) {
		OnWindow(ad_run_inference(&mState), centi);
	}

	if (mLastResult.phase == AD_LEARNING) {
		LOG_INF("(%02u:%02u:%02u, %d.%02d C, %s) recognising %u/%u min", seconds / 3600, (seconds / 60) % 60,
			seconds % 60, centi / 100, abs(centi % 100), mAlarmOn ? "true" : "false", mState.k, AD_RECOG);
		return;
	}

	const int32_t level = Centi(mState.L0);
	const int32_t score = Tenths(mLastResult.score);
	LOG_INF("(%02u:%02u:%02u, %d.%02d C, %s) level %d.%02d C score %d.%d [%s]", seconds / 3600,
		(seconds / 60) % 60, seconds % 60, centi / 100, abs(centi % 100), mAlarmOn ? "true" : "false",
		level / 100, abs(level % 100), score / 10, abs(score % 10), PhaseName(mLastResult.phase));
}

void Judge::OnWindow(const ad_result_t &result, int16_t centi)
{
	const uint8_t previousPhase = mLastResult.phase;
	mLastResult = result;

	if (previousPhase == AD_LEARNING && result.phase != AD_LEARNING) {
		const int32_t level = Centi(mState.L0);
		LOG_INF("[model] recognised %d.%02d C after %u min -> BASIC: judging against the recognised level",
			level / 100, abs(level % 100), AD_RECOG);
	}
	if (previousPhase == AD_BASIC && result.phase == AD_FULL) {
		LOG_INF("[model] daily profile learned -> FULL: judging against the time-of-day profile");
	}
	if (result.phase == AD_LEARNING) {
		return;
	}

	const int32_t score = Tenths(result.score);

	if (result.anomaly) {
		mNormalStreak = 0;
		if (!mAlarmOn) {
			LOG_WRN("[model] ANOMALY score %d.%d temp %d.%02d C [%s] -> alarm ON", score / 10, abs(score % 10),
				centi / 100, abs(centi % 100), PhaseName(result.phase));
			SetAlarm(true);
		}
		return;
	}

	mNormalStreak++;
	if (mAlarmOn && mNormalStreak >= kAlarmClearWindows) {
		LOG_INF("[model] normal again (score %d.%d) -> alarm OFF", score / 10, abs(score % 10));
		SetAlarm(false);
	}
}

/* Matter thread only. */
void Judge::SetAlarm(bool on)
{
	mAlarmOn = on;
	SetAlarmLed(on);

	Protocols::InteractionModel::Status status = OnOff::Attributes::OnOff::Set(kAlarmEndpointId, on);
	if (status != Protocols::InteractionModel::Status::Success) {
		LOG_ERR("Updating the alarm OnOff attribute failed %x", to_underlying(status));
	}
}

void Judge::OnAlarmAttributeWritten(bool on)
{
	SetAlarmLed(on);
}

void Judge::SetAlarmLed(bool on)
{
	Nrf::GetBoard().GetLED(kAlarmLed).Set(on);
}
