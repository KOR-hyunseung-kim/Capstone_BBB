# WiFi 구현 디버깅 및 ESP32 배포

**Date**: 2026-05-06 (연속 작업)  
**Status**: 진행 중 (ESP32 테스트 대기)  
**Scope**: WiFi 통신 버그 픽스 및 MicroPython 호환성 개선

## 작업 요약

완성된 WiFi 구현을 실제 ESP32에 배포하면서 발견된 MicroPython 호환성 문제를 해결.

## 문제점 및 해결

### 1. traceback 모듈 미존재

**문제**: boot.py에서 `import traceback` 시도
```python
import traceback
traceback.print_exc()
```

**에러 메시지**:
```
[Error] Failed to start main: 'module' object has no attribute 'network'
Traceback (most recent call last):
  ...
ImportError: no module named 'traceback'
```

**원인**: MicroPython에는 표준 `traceback` 모듈이 없음

**해결책**: 
- boot.py에서 traceback import 제거
- 간단한 에러 메시지만 출력하도록 수정

**수정된 boot.py**:
```python
try:
    import main
except Exception as e:
    print(f"[Error] Failed to start main: {e}")
    # traceback 사용 안 함
```

### 2. network 모듈 조건부 로딩

**문제**: `import network`가 실패해도 계속 사용하려고 함
```python
import network  # ← 실패하면 여기서 멈춤
self.wlan = network.WLAN(...)  # ← 실행 안 됨
```

**에러 메시지**:
```
[Init] WiFi... FAILED ('WiFiManager' object has no attribute 'connect')
```

**원인**: network import 실패 시 WiFiManager 객체가 불완전하게 생성됨

**해결책**: 
- network import를 try/except로 안전하게 처리
- WiFiManager.__init__에서 network 확인 후 오류 발생

**수정된 wifi.py**:
```python
try:
    import network
    HAS_NETWORK = True
except ImportError:
    print("[Warning] network module not available")
    HAS_NETWORK = False

class WiFiManager:
    def __init__(self, ssid, password):
        if not HAS_NETWORK:
            raise RuntimeError("network module not available")
        # 이후 코드...
```

### 3. 메서드 누락

**문제**: WiFiManager에 `connect()`, `disconnect()` 등 메서드가 없음

**원인**: 파일 편집 중 메서드 부분이 누락됨

**해결책**: 전체 wifi.py를 다시 작성
- WiFiManager: connect, disconnect, get_ip, is_connected
- UDPComm: init_transmitter, send_emg_data, send_monitoring_data, close

## 수정된 파일

### firmware/boot.py
- traceback import 제거
- 간단한 에러 처리로 변경
- 라인: 18 → 17

### firmware/comm/wifi.py
- network import를 try/except로 감싸기
- WiFiManager에 HAS_NETWORK 체크 추가
- 모든 메서드 복원: connect, disconnect, get_ip, is_connected
- UDPComm 모든 메서드 포함: send_emg_data, send_monitoring_data, recv_analysis_result, close
- 라인: 194 (완전 재작성)

## 배포 체크리스트

- [x] boot.py traceback 제거
- [x] wifi.py network import 안전화
- [x] wifi.py 모든 메서드 복원
- [ ] Thonny에서 두 파일 업로드
- [ ] ESP32 RESET 버튼 눌러 재부팅
- [ ] Console 출력 확인

## 예상되는 부팅 시퀀스

성공 시:
```
[Boot] Starting BBB firmware...
[Init] Initializing hardware...
[Init] EMG sensor... OK
[Init] Vibration motor... OK
[Init] RGB LED... OK
[Init] OLED display... OK
[Init] WiFi... OK
[WiFi] Connected: 192.168.x.x

[Calib] Entering calibration in 3 seconds...
[Calib] Starting 60s calibration...
[Monitor] Calibration complete. Starting monitoring...
```

실패 시 에러 메시지와 함께 구체적인 단계 표시됨

## 다음 단계

### 즉시 (필수)
1. Thonny에서 파일 업로드
2. ESP32 RESET 및 부팅 확인
3. WiFi 연결 상태 확인
4. 데이터 수신 테스트 (`python tools/test_wifi_connection.py`)

### 진행 중 (진단용)
1. PC IP 정확성 확인 (`ipconfig`)
2. 방화벽 설정 확인
3. Dashboard 서버 실행 확인

### 완료 후 (분석)
1. 실제 EMG 신호 품질 테스트
2. 팔 움직임에 따른 피로도 반응 확인
3. LED/Motor 피드백 동작 검증

## MicroPython 호환성 주의사항

배운 점:
1. `traceback` 모듈 사용 불가 → try/except로 간단히 처리
2. 표준 라이브러리 대부분 없음 → import 시 try/except 필수
3. 메모리 제약 심함 → 디버그 코드도 최소화
4. 네트워크 모듈은 특정 보드에서만 사용 가능

## 문제 진단 과정

1. **콘솔 에러 메시지 읽기** → `network` 모듈 없음 파악
2. **Thonny Python vs MicroPython 구분** → 표준 Python 환경에서 테스트 불가
3. **파일 부분 수정 문제** → 메서드 누락 발생 → 전체 재작성으로 해결
4. **방어적 프로그래밍** → try/except로 모든 import 감싸기

## 파일 통계

| 파일 | 변경 | 상태 |
|------|------|------|
| firmware/boot.py | 수정 | 완료 |
| firmware/comm/wifi.py | 재작성 | 완료 |
| firmware/config.py | 변경 없음 | OK |
| firmware/main.py | 변경 없음 | OK |
| 기타 firmware/* | 변경 없음 | OK |

## 예상 소요 시간

- 파일 수정: ✅ 완료
- Thonny 업로드: 2-3분
- 부팅 및 확인: 2-3분
- WiFi 연결 테스트: 1-2분
- **총 예상**: 5-10분

## 문서 참조

- [WiFi 트러블슈팅](../WIFI_TROUBLESHOOTING.md)
- [WiFi 셋업](../WIFI_SETUP.md)
- [검증 체크리스트](../VERIFICATION_CHECKLIST.md)
- [WiFi 테스트 스크립트](../../tools/test_wifi_connection.py)

## 다음 세션 시작 가이드

다음 작업 시작 시:
1. Thonny 열기
2. firmware/comm/wifi.py, firmware/boot.py 업로드 확인
3. ESP32 콘솔 부팅 메시지 확인
4. 필요시 추가 디버깅 진행

---

**Status**: 파일 수정 완료, ESP32 배포 대기  
**Next**: Thonny 업로드 및 부팅 테스트  
**Last Updated**: 2026-05-06
