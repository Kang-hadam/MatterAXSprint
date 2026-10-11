# MatterAXSprint

10/15 matter ax sprint 대회 레포지토리

센서 펌웨어가 보낸 데이터로 위기 신호를 판단하고, 그 결과를 앱에 띄운다.

| 디렉터리 | 내용 |
|----------|------|
| [`firmware/`](firmware) | nRF Connect SDK(Zephyr) 펌웨어 |
| [`app/`](app) | 앱 — Next.js(vinext) 프론트 + Rust(Axum) API, bun 워크스페이스 |

## firmware

nRF Connect SDK v3.3.4 기준.

| 프로젝트 | 보드 | 내용 |
|----------|------|------|
| `blinky` | — | LED 점멸 예제 |
| `dongle_sensor` | nRF52840 Dongle | 외부 센서 핀 스캔, 칩 내장 온도를 USB 시리얼로 출력 |
| `temp_alarm/sensor_dongle` | nRF52840 Dongle | 칩 내장 온도를 1초마다 Thread로 전송 |
| `temp_alarm/led_dk` | nRF54LM20-DK | Thread로 온도를 받아 기준치를 넘으면 LED0 점등 |
| `temp_alarm/common` | — | 두 보드가 공유하는 Thread 네트워크 설정 |
| `thread_cli/ot.ps1` | — | 시리얼 포트로 OpenThread CLI 명령 전송 |

빌드 예시:

```sh
west build -b nrf52840dongle/nrf52840 firmware/temp_alarm/sensor_dongle
west build -b nrf54lm20dk/nrf54lm20b/cpuapp firmware/temp_alarm/led_dk
```

빌드 산출물(`build*/`)은 커밋하지 않는다.

## app

```sh
cd app
bun install
cd apps/front && bun dev
```

자세한 규칙은 [`app/AGENTS.md`](app/AGENTS.md).
