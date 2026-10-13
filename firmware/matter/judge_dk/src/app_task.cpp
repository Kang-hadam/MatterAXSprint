/*
 * Matter judge node on the nRF54LM20-DK.
 *
 * Based on nrf/samples/matter/light_switch (Nordic-5-Clause).
 */

#include "app_task.h"

#include "judge.h"
#include "shell_commands.h"
#include "status_log.h"

#include "app/matter_init.h"
#include "app/task_executor.h"
#include "board/board.h"
#include "clusters/identify.h"

#include <zephyr/logging/log.h>

LOG_MODULE_DECLARE(app, CONFIG_CHIP_APP_LOG_LEVEL);

using namespace ::chip;
using namespace ::chip::app;
using namespace ::chip::DeviceLayer;

namespace
{
Nrf::Matter::IdentifyCluster sIdentifyClusterBinding(Judge::kBindingEndpointId);
Nrf::Matter::IdentifyCluster sIdentifyClusterAlarm(Judge::kAlarmEndpointId);

#ifdef CONFIG_CHIP_ICD_UAT_SUPPORT
#define UAT_BUTTON_MASK DK_BTN3_MSK
#endif
} /* namespace */

/* Buttons 1 (factory reset / software update) are handled by the board
 * module's default handler. */
void AppTask::ButtonEventHandler(Nrf::ButtonState state, Nrf::ButtonMask hasChanged)
{
#ifdef CONFIG_CHIP_ICD_UAT_SUPPORT
	if (UAT_BUTTON_MASK & state & hasChanged) {
		LOG_INF("ICD UserActiveMode has been triggered.");
		Server::GetInstance().GetICDManager().OnNetworkActivity();
	}
#else
	ARG_UNUSED(state);
	ARG_UNUSED(hasChanged);
#endif
}

CHIP_ERROR AppTask::Init()
{
	/* Initialize Matter stack. The binding manager needs the server, so the
	 * judge is initialized from the post-server-init callback. */
	ReturnErrorOnFailure(Nrf::Matter::PrepareServer(Nrf::Matter::InitData{ .mPostServerInitClbk = [] {
		Judge::Instance().Init();
		JudgeCommands::Register();
		return CHIP_NO_ERROR;
	} }));

	if (!Nrf::GetBoard().Init(ButtonEventHandler)) {
		LOG_ERR("User interface initialization failed.");
		return CHIP_ERROR_INCORRECT_STATE;
	}

	/* Register Matter event handler that controls the connectivity status LED based on the captured Matter network
	 * state. */
	ReturnErrorOnFailure(Nrf::Matter::RegisterEventHandler(Nrf::Board::DefaultMatterEventHandler, 0));
	ReturnErrorOnFailure(StatusLog::Init());

	ReturnErrorOnFailure(sIdentifyClusterBinding.Init());
	ReturnErrorOnFailure(sIdentifyClusterAlarm.Init());

	ReturnErrorOnFailure(Nrf::Matter::StartServer());
	StatusLog::PrintCurrent();
	return CHIP_NO_ERROR;
}

CHIP_ERROR AppTask::StartApp()
{
	ReturnErrorOnFailure(Init());

	while (true) {
		Nrf::DispatchNextTask();
	}

	return CHIP_NO_ERROR;
}
