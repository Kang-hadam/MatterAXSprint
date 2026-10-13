/*
 * Project-specific overrides of the default Matter (CHIP) configuration.
 */

#pragma once

/* One CASE session to the sensor is all this node ever opens as a client. */
#define CHIP_CONFIG_CONTROLLER_MAX_ACTIVE_DEVICES 2
