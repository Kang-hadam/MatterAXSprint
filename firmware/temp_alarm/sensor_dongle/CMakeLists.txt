# SPDX-License-Identifier: Apache-2.0

cmake_minimum_required(VERSION 3.20.0)
find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(temp_sensor_dongle)

target_sources(app PRIVATE src/main.c ../common/thread_net.c)
target_include_directories(app PRIVATE ../common)
