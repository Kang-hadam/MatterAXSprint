# MatterAXSprint

10/15 matter ax sprint 대회 레포지토리

센서 펌웨어가 보낸 데이터로 위기 신호를 판단하고, 그 결과를 앱에 띄운다.

| 디렉터리 | 내용 |
|----------|------|
| [`firmware/`](firmware) | nRF Connect SDK(Zephyr) 펌웨어 |
| [`docs/demo-setup.md`](docs/demo-setup.md) | 시연 세팅 절차 (플래시 → 커미셔닝 → 로그) |
| [`tools/border-router/`](tools/border-router) | 라즈베리파이 — Thread Border Router(OTBR) + Matter 컨트롤러(chip-tool) + 앱 API 브리지 |
| [`app/`](app) | 앱 — Next.js(vinext) 프론트 + Rust(Axum) API, bun 워크스페이스 |

## Matter 구성

```
[동글] 온도 센서 (TemperatureMeasurement 서버)
   │ Thread/Matter, 1초마다 읽힘 (Binding)
   ▼
[DK]  온디바이스 AI 이상 판정 (5분 인식 → 매분 판정) → 자기 OnOff 속성 = 알람, LED
   │ Thread
   ▼
[라즈베리파이] OTBR(RCP 동글) + chip-tool: 커미셔닝(인증서 발급), ACL/Binding 설정, 상태 구독
   │ HTTP
   ▼
[Axum API] → [앱]
```

| 역할 | 하드웨어 | 펌웨어 / 소프트웨어 |
|------|----------|---------------------|
| 온도 센서 (Matter 노드 1) | nRF52840 Dongle | `firmware/matter/sensor_dongle` |
| 판정 보드 (Matter 노드 2) | nRF54LM20-DK | `firmware/matter/judge_dk` |
| Border Router RCP | nRF52840 Dongle (두 번째) | NCS `samples/openthread/coprocessor` 그대로 |
| Border Router + 컨트롤러 | Raspberry Pi 4 | `tools/border-router` |

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
| `matter/sensor_dongle` | nRF52840 Dongle | Matter 온도 센서 노드 (칩 내장 온도, 1초 갱신) |
| `matter/judge_dk` | nRF54LM20-DK | Matter 판정 노드 — Binding으로 센서 온도를 읽어 이상 탐지 모델에 넣고, 이상이면 OnOff 속성 ON + LED |
| `anomaly/` | — | 온도 이상 탐지 모델: PyTorch 학습(`ml/`), C 런타임(`src/`, judge_dk가 링크), 보드 자체 검증(`selftest/`) |

빌드 예시:

```sh
west build -b nrf52840dongle/nrf52840 firmware/temp_alarm/sensor_dongle
west build -b nrf54lm20dk/nrf54lm20b/cpuapp firmware/temp_alarm/led_dk
```

Matter 펌웨어는 헤더 경로가 길어 Windows의 260자 제한에 걸리므로 **빌드 디렉터리를 짧은 경로에** 둔다:

```sh
west build -b nrf52840dongle/nrf52840      -d C:\ncs\tmp\mts firmware/matter/sensor_dongle
west build -b nrf54lm20dk/nrf54lm20b/cpuapp -d C:\ncs\tmp\mjd firmware/matter/judge_dk
```

빌드 산출물(`build*/`)은 커밋하지 않는다.

### 이상 탐지 모델 (`firmware/anomaly`)

센서가 설치된 공간을 **처음 5분** 동안 인식(수준·변동·노이즈)하고, 이후 매 1분 창을 인식된 기준
(BASIC) 또는 하루치 프로파일(FULL)과 비교해 점수를 낸다. 264개 파라미터, float32, libm·heap 없음.
모델 상수를 바꾸면 `ml/train.py`로 `src/anomaly_model.h`를 다시 생성한다. 자세한 내용은
[`firmware/anomaly/README.md`](firmware/anomaly/README.md).

## app

```sh
cd app
bun install
cd apps/front && bun dev
```

자세한 규칙은 [`app/AGENTS.md`](app/AGENTS.md).
