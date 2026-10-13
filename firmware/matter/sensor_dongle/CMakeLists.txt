#
# Matter temperature sensor on the nRF52840 Dongle.
#
# Based on nrf/samples/matter/temperature_sensor (Nordic-5-Clause).
#

cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr HINTS $ENV{ZEPHYR_BASE})

project(ansim-sensor-dongle)

# Enable GNU STD support.
include(${ZEPHYR_CONNECTEDHOMEIP_MODULE_DIR}/config/nrfconnect/app/enable-gnu-std.cmake)

# Include all source files that are located in the Matter common directory.
include(${ZEPHYR_NRF_MODULE_DIR}/samples/matter/common/cmake/source_common.cmake)

# Include Data Model utils
include(${ZEPHYR_NRF_MODULE_DIR}/samples/matter/common/cmake/data_model.cmake)

include(${ZEPHYR_NRF_MODULE_DIR}/samples/matter/common/cmake/zap_helpers.cmake)
ncs_get_zap_parent_dir(ZAP_PARENT_DIR)

target_include_directories(app PRIVATE
  src
  ${CMAKE_CURRENT_SOURCE_DIR}/../common
  ${ZAP_PARENT_DIR}
)

target_sources(app PRIVATE
  src/app_task.cpp
  src/main.cpp
  ${CMAKE_CURRENT_SOURCE_DIR}/../common/status_log.cpp
)

ncs_configure_data_model()
