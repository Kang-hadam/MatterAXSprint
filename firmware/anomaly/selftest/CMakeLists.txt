cmake_minimum_required(VERSION 3.20.0)

find_package(Zephyr REQUIRED HINTS $ENV{ZEPHYR_BASE})
project(ansim_anomaly_selftest)

set(AD_SRC ${CMAKE_CURRENT_SOURCE_DIR}/../src)

target_include_directories(app PRIVATE ${AD_SRC} src)
target_sources(app PRIVATE src/main.c src/test_data.c ${AD_SRC}/anomaly.c)
# no fused multiply-add: the detector must reproduce ml/features.py bit for bit
set_source_files_properties(${AD_SRC}/anomaly.c PROPERTIES COMPILE_OPTIONS -ffp-contract=off)
