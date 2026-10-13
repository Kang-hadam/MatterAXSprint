/*
 * One-line, human readable progress of a Matter node on the serial log:
 * waiting for the controller, certificate received, mesh joined, ...
 * Shared by the sensor dongle and the judge board.
 */

#pragma once

#include <lib/core/CHIPError.h>

namespace StatusLog
{
/* Call after Nrf::Matter::PrepareServer(); prints the boot state and
 * follows connectivity and commissioning events from then on. */
CHIP_ERROR Init();

/* Prints the current state once (used right after the server started). */
void PrintCurrent();
} /* namespace StatusLog */
