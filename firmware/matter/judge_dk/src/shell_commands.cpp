/*
 * "judge" shell commands:
 *   judge status   last temperature, model phase, score and alarm state
 *   judge table    binding table (which sensor this node reads)
 */

#include "shell_commands.h"

#include "binding/binding_handler.h"
#include "judge.h"

#include <lib/shell/Engine.h>
#include <lib/shell/commands/Help.h>
#include <lib/shell/streamer.h>

#include <cstdlib>

#ifdef CONFIG_CHIP_LIB_SHELL

namespace JudgeCommands
{
using chip::Shell::Engine;
using chip::Shell::shell_command_t;
using chip::Shell::streamer_get;
using chip::Shell::streamer_printf;

namespace
{
Engine sSubCommands;

CHIP_ERROR HelpHandler(int argc, char **argv)
{
	sSubCommands.ForEachCommand(chip::Shell::PrintCommandHelp, nullptr);
	return CHIP_NO_ERROR;
}

CHIP_ERROR JudgeHandler(int argc, char **argv)
{
	if (argc == 0) {
		return HelpHandler(argc, argv);
	}
	return sSubCommands.ExecCommand(argc, argv);
}

int32_t Tenths(float value)
{
	return static_cast<int32_t>(value * 10.0f + 0.5f);
}

CHIP_ERROR StatusHandler(int argc, char **argv)
{
	Judge &judge = Judge::Instance();

	if (!judge.HasReading()) {
		streamer_printf(streamer_get(), "no reading from the sensor yet\r\n");
		return CHIP_NO_ERROR;
	}

	int16_t temp = judge.LastTemperature();
	streamer_printf(streamer_get(), "temp %d.%02d C, alarm %s, window %u (%u/%u samples)\r\n", temp / 100,
			abs(temp % 100), judge.AlarmOn() ? "ON" : "OFF", judge.WindowsCompleted(), judge.SamplesInWindow(),
			AD_WINDOW);

	if (judge.Phase() == AD_LEARNING) {
		streamer_printf(streamer_get(), "model: recognising the space, %u/%u min\r\n", judge.WindowsCompleted(),
				AD_RECOG);
		return CHIP_NO_ERROR;
	}

	int32_t level = static_cast<int32_t>(judge.RecognisedLevel() * 100.0f);
	int32_t score = Tenths(judge.LastScore());
	int32_t thr = Tenths(judge.Phase() == AD_FULL ? ad_thr_full : ad_thr_basic);
	streamer_printf(streamer_get(), "model: %s, recognised level %d.%02d C, score %d.%d (threshold %d.%d)\r\n",
			judge.Phase() == AD_FULL ? "FULL (daily profile)" : "BASIC (recognised level)", level / 100,
			abs(level % 100), score / 10, score % 10, thr / 10, thr % 10);
	return CHIP_NO_ERROR;
}

CHIP_ERROR TableHandler(int argc, char **argv)
{
	Nrf::Matter::BindingHandler::PrintBindingTable();
	return CHIP_NO_ERROR;
}
} /* namespace */

void Register()
{
	static const shell_command_t sSubCommandList[] = {
		{ &HelpHandler, "help", "Judge commands" },
		{ &StatusHandler, "status", "Print last temperature, model phase/score and alarm state" },
		{ &TableHandler, "table", "Print the binding table" },
	};

	static const shell_command_t sCommand = { &JudgeHandler, "judge",
						  "Temperature judge commands. Usage: judge [status|table]" };

	sSubCommands.RegisterCommands(sSubCommandList, MATTER_ARRAY_SIZE(sSubCommandList));
	Engine::Root().RegisterCommands(&sCommand, 1);
}

} /* namespace JudgeCommands */

#else

namespace JudgeCommands
{
void Register()
{
}
} /* namespace JudgeCommands */

#endif /* CONFIG_CHIP_LIB_SHELL */
