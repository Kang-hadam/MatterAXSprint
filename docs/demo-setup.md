# 시연 세팅 절차 (처음부터: 플래시 → 커미셔닝 → 로그 확인)

"시연 세팅 준비해" 요청 시 이 문서 순서대로 진행한다.
1~3단계는 에이전트가, 4~5단계는 사람이 (또는 요청 시 에이전트가) 수행한다.

## 전제

| 항목 | 값 |
|---|---|
| DK (판정, Matter 노드 2) | nRF54LM20-DK, J-Link S/N `1051837576`, 로그 **COM13** |
| 센서 동글 (Matter 노드 1) | nRF52840 Dongle, 앱 모드 **COM15**, 부트로더 모드 **COM14** |
| 라즈베리파이 (보더라우터 + 컨트롤러) | `devfive@192.168.0.65`, SSH 키 등록됨, 스크립트 `~/ansim` |
| RCP 동글 | 라즈베리파이 USB에 꽂혀 있음 (`Thread Co-Processor`) |
| 빌드 산출물 | DK `C:\ncs\tmp\mjd`, 동글 `C:\ncs\tmp\mts` (없으면 아래 "빌드" 먼저) |
| 작업 디렉터리 | PC `C:\Users\xldi2\WebstormProjects\ansim-loop` |

사전 점검 (에이전트):
```powershell
nrfutil device list        # J-Link(COM12) + Ansim Matter Temp Sensor(COM15) 또는 Open DFU Bootloader(COM14)
Test-Connection 192.168.0.65 -Count 1 -Quiet
ssh devfive@192.168.0.65 "sudo docker exec otbr ot-ctl state | head -1; hciconfig hci0 | grep -oE 'UP|DOWN'"
# 기대: leader (또는 router), UP
```
`otbr`가 안 떠 있으면 `sudo systemctl restart otbr` 후 `~/ansim/thread-up.sh`. Bluetooth가 DOWN이면
`sudo rfkill unblock bluetooth; sudo hciconfig hci0 up`.

## (필요 시) 빌드

펌웨어를 고쳤을 때만. 빌드 디렉터리는 반드시 짧은 경로.
```powershell
cd C:\ncs\v3.3.4
nrfutil sdk-manager toolchain launch --ncs-version v3.3.4 -- west build -b nrf54lm20dk/nrf54lm20b/cpuapp -d C:\ncs\tmp\mjd C:\Users\xldi2\WebstormProjects\ansim-loop\firmware\matter\judge_dk
nrfutil sdk-manager toolchain launch --ncs-version v3.3.4 -- west build -b nrf52840dongle/nrf52840 -d C:\ncs\tmp\mts C:\Users\xldi2\WebstormProjects\ansim-loop\firmware\matter\sensor_dongle
```
각 5~10분. 로그가 길어서 파일로 리다이렉트하고 `error:|FLASH:`만 grep 한다.

## 1. DK 전체 삭제 + 플래시 (커미셔닝 정보 삭제됨)

```powershell
cd C:\ncs\v3.3.4
nrfutil sdk-manager toolchain launch --ncs-version v3.3.4 -- west flash -d C:\ncs\tmp\mjd --erase
```
끝에 `flashed successfully`. 자동 리셋.

`--erase` 없이 `merged.hex`를 쓰면 MCUboot 보호 영역 때문에
`Address 0x00000000 is in a protected RRAMC region`으로 실패한다. 커미셔닝을 유지한 채
앱만 바꾸려면:
```powershell
nrfutil sdk-manager toolchain launch --ncs-version v3.3.4 -- west flash -d C:\ncs\tmp\mjd --hex-file C:\ncs\tmp\mjd\judge_dk\zephyr\zephyr.signed.hex
```

## 2. 센서 동글 플래시 + 공장초기화

2-1. 부트로더 진입 (이미 COM14면 건너뜀):
```powershell
cd C:\Users\xldi2\WebstormProjects\ansim-loop
tools\serial-log.ps1 COM15 -Seconds 3 -Send "gpio conf gpio@50000000 19 o0"
```
안 되면 동글 옆면 리셋 버튼. 빨간 LED가 숨쉬고 포트가 COM14로 바뀜.

2-2. DFU 패키지 생성 + 전송:
```powershell
nrfutil nrf5sdk-tools pkg generate --hw-version 52 --sd-req 0x00 --application C:\ncs\tmp\mts\sensor_dongle\zephyr\zephyr.hex --application-version 1 C:\ncs\tmp\mts\sensor_dongle.zip
nrfutil nrf5sdk-tools dfu usb-serial -pkg C:\ncs\tmp\mts\sensor_dongle.zip -p COM14
```
`Device programmed.` 후 10초쯤 뒤 COM15로 복귀.

2-3. 공장초기화 (DFU는 settings 영역을 안 지우므로 커미셔닝 정보가 남아 있음):
```powershell
tools\serial-log.ps1 COM15 -Seconds 15 -Send "matter device factoryreset"
```
재부팅 후 `[status] waiting for the border router (controller) to commission this node...` 확인.

## 3. 라즈베리파이 컨트롤러 기억 삭제

```powershell
ssh devfive@192.168.0.65 "rm -rf ~/chip-tool-storage/*"
```
chip-tool이 노드 1·2를 기억하고 있으면 새 커미셔닝이 꼬인다.

여기까지 끝나면 DK(COM13)·동글(COM15) 로그 모두
`[status] waiting for the border router (controller) to commission this node...` 상태.

## 4. 로그 창 띄우기 (PC, PowerShell 두 개)

```powershell
cd C:\Users\xldi2\WebstormProjects\ansim-loop
tools\serial-log.ps1 COM13     # DK: [status] 단계 + (시간, 온도, 이상여부)
tools\serial-log.ps1 COM15     # 동글: [status] + 원시 온도
```
Ctrl+C로 종료. 에이전트가 포트를 읽는 중이면 "Access to the path is denied"가 나므로 한쪽만 연다.

## 5. 커미셔닝 (라즈베리파이)

```
ssh devfive@192.168.0.65
cd ~/ansim
./commission.sh
```
동글 등록 → DK 등록 → 동글 ACL → DK Binding → 검증 읽기. 2~3분.

PC 로그에 순서대로 보여야 하는 것:
```
[status] controller connected, receiving fabric certificate...
[status] certificate received, joined the Matter fabric
[status] joining the Thread mesh...
[status] on the Thread mesh, reachable through the border router
[status] no sensor bound yet, waiting for the controller to write the binding   (DK)
[status] sensor connected over Thread, reading temperature every 1 s           (DK)
(00:01:23, 23.75 C, false) recognising 1/5 min                                (DK, 1초마다, 첫 5분)
[model] recognised 23.75 C after 5 min -> BASIC: judging against the recognised level
(00:06:01, 23.80 C, false) level 23.75 C score 0.8 [BASIC]                    (DK, 1초마다)
```

실패 시:
- BLE 타임아웃 / `Device commissioning Failure` → 그 노드만 재시도:
  `./commission.sh ble sensor` 또는 `./commission.sh ble judge`, 성공 후 `./commission.sh ble link`
- `networkingStatus=2` → 보드 공장초기화 후 재시도 (동글: 2-3, DK: 1단계)
- `org.bluez.Error.NotReady` → 라즈베리파이 Bluetooth가 꺼짐, 사전 점검 참고

## 시연

DK 로그를 보면서 동글 칩에 라이터를 가까이 댄다. 판정은 온디바이스 이상 탐지 모델이 한다:

1. 센서 연결 후 **첫 5분**은 공간 인식 (`recognising n/5 min`) — 이 동안은 알람이 나지 않으니 덥히지 말 것.
2. 인식이 끝나면 매 1분 창마다 점수를 낸다. 점수가 임계치(BASIC 5.1)를 넘는 분에 `[model] ANOMALY ...`
   + `true` + DK LED2 점등, 다시 정상으로 판정된 분에 `false`. 응답 단위는 1분이다.
3. 센서가 30초 이상 끊기면 모델 상태를 버리고 5분 인식을 다시 한다.

(LED1은 패브릭 연결 상태라 평소에도 켜져 있음.) 셸에서 `judge status`로 현재 phase/점수/임계치 확인.

컨트롤러에서 직접 읽기 (라즈베리파이):
```
cd ~/ansim && source env.sh
ct onoff read on-off 2 2                          # 알람
ct temperaturemeasurement read measured-value 1 1 # 온도 (0.01 °C)
```

## 알려진 문제

- DK가 가끔 시리얼 무응답으로 멈춘 적 있음 (동글 재부팅 직후). `nrfutil device reset --serial-number 1051837576`으로 복구, 커미셔닝은 유지됨.
  로그와 셸 에코가 **둘 다** 멈췄다면 보드가 fatal error로 halt된 것이다 (`CONFIG_RESET_ON_FATAL_ERROR=n`). 이전 judge 펌웨어는
  읽기마다 `BindingData`를 누수해 부팅 5분 25초쯤 Matter 힙 고갈로 `abort()`했다 — 아마 위 "시리얼 무응답"의 실제 원인 (수정됨).
  시리얼 없이 halt 여부를 보려면 `nrfutil device read --serial-number 1051837576 --address <addr> --bytes 16 --width 32 --direct`를
  두 번 읽어 `mState.k`/`n`이 변하는지 본다 (`<addr>`: `arm-zephyr-eabi-gdb zephyr.elf -batch -ex "print &'Judge::Instance()::sJudge'.mState.k"`).
- 라즈베리파이 `nrfutil`(pip 5.2.0)은 Python 3.12에서 깨져 있어 `~/.local/lib/python3.12/site-packages/nordicsemi/dfu/dfu_transport_serial.py`를 손으로 고친 상태. RCP 동글을 다시 플래시할 일이 생기면 PC에서 `nrfutil nrf5sdk-tools dfu usb-serial -pkg C:\ncs\tmp\rcp\rcp_dongle.zip -p COMx`로 하는 게 편하다.
