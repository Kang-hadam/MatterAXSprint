#include "status_log.h"

#include "app/matter_event_handler.h"

#include <app/server/Server.h>
#include <platform/CHIPDeviceLayer.h>
#include <platform/ConnectivityManager.h>

#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

using namespace chip;
using namespace chip::DeviceLayer;

namespace
{
enum class Phase : uint8_t { Unknown, WaitingForController, ControllerConnected, Certified, JoiningMesh, OnMesh };

Phase sPhase = Phase::Unknown;

bool HasFabric()
{
	return Server::GetInstance().GetFabricTable().FabricCount() > 0;
}

bool OnMesh()
{
	return ConnectivityMgr().IsThreadAttached();
}

void Show(Phase phase)
{
	if (phase == sPhase) {
		return;
	}
	sPhase = phase;

	switch (phase) {
	case Phase::WaitingForController:
		LOG_INF("[status] waiting for the border router (controller) to commission this node...");
		break;
	case Phase::ControllerConnected:
		LOG_INF("[status] controller connected, receiving fabric certificate...");
		break;
	case Phase::Certified:
		LOG_INF("[status] certificate received, joined the Matter fabric");
		break;
	case Phase::JoiningMesh:
		LOG_INF("[status] joining the Thread mesh...");
		break;
	case Phase::OnMesh:
		LOG_INF("[status] on the Thread mesh, reachable through the border router");
		break;
	default:
		break;
	}
}

void Evaluate()
{
	if (OnMesh()) {
		Show(Phase::OnMesh);
	} else if (HasFabric()) {
		Show(Phase::JoiningMesh);
	} else if (ConnectivityMgr().NumBLEConnections() != 0) {
		Show(Phase::ControllerConnected);
	} else {
		Show(Phase::WaitingForController);
	}
}

void OnEvent(const ChipDeviceEvent *event, intptr_t)
{
	switch (event->Type) {
	case DeviceEventType::kCHIPoBLEConnectionEstablished:
		Show(Phase::ControllerConnected);
		break;
	case DeviceEventType::kCommissioningComplete:
		Show(Phase::Certified);
		Evaluate();
		break;
	case DeviceEventType::kThreadStateChange:
		if (event->ThreadStateChange.RoleChanged) {
			Evaluate();
		}
		break;
	case DeviceEventType::kThreadConnectivityChange:
	case DeviceEventType::kCHIPoBLEAdvertisingChange:
	case DeviceEventType::kCHIPoBLEConnectionClosed:
	case DeviceEventType::kServerReady:
		Evaluate();
		break;
	default:
		break;
	}
}
} /* namespace */

namespace StatusLog
{
CHIP_ERROR Init()
{
	return Nrf::Matter::RegisterEventHandler(OnEvent, 0);
}

void PrintCurrent()
{
	if (HasFabric()) {
		LOG_INF("[status] already commissioned (fabric stored in flash)");
	}
	Evaluate();
}
} /* namespace StatusLog */
