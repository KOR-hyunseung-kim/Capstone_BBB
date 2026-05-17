# 디버그 모드 사용 가이드

ESP32-S3에서 각 장치를 독립적으로 테스트하고 디버그 정보를 출력할 수 있습니다.

---

## 📋 **Debug 설정 (firmware/config.py)**

### **기본 설정**
```python
DEBUG = True  # 전체 디버그 모드 활성화

# 각 장치 활성화/비활성화
ENABLE_EMG_SENSOR = True   # EMG 센서 사용
ENABLE_MOTOR = True        # 진동모터 사용
ENABLE_LED = True          # RGB LED 사용
ENABLE_OLED = True         # OLED 디스플레이 사용

# 디버그 출력 옵션
DEBUG_EMG_VALUES = True     # RMS 값 출력
DEBUG_LED_CONTROL = True    # LED 제어 신호 출력
DEBUG_MOTOR_CONTROL = True  # 모터 제어 신호 출력
DEBUG_OLED_UPDATES = True   # OLED 업데이트 정보 출력
DEBUG_INTERVAL_CYCLES = 1   # 매 사이클마다 출력 (1 = 매번, 10 = 10번마다)
```

---

## 🎯 **사용 사례별 설정**

### **Case 1: EMG 센서만 테스트**
```python
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = False
ENABLE_LED = False
ENABLE_OLED = False

DEBUG_EMG_VALUES = True
DEBUG_INTERVAL_CYCLES = 1  # 매번 출력
```

**출력 예시:**
```
[Cycle 1]
  [EMG] RMS= 2010.5 | Signal=100.0% baseline
  [Fatigue] [OK] NORMAL
  [Motor] OFF (normal)

[Cycle 2]
  [EMG] RMS= 2015.3 | Signal=100.2% baseline
  [Fatigue] [OK] NORMAL
  [Motor] OFF (normal)
```

---

### **Case 2: LED 제어만 테스트**
```python
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = False
ENABLE_LED = True
ENABLE_OLED = False

DEBUG_EMG_VALUES = True
DEBUG_LED_CONTROL = True
DEBUG_INTERVAL_CYCLES = 1
```

**출력 예시:**
```
[Cycle 1]
  [EMG] RMS= 2010.5 | Signal=100.0% baseline
  [Fatigue] [OK] NORMAL
  [LED] Set to GREEN (0, 1023, 0)
  [Motor] OFF (normal)

[Cycle 5]
  [EMG] RMS= 1700.3 | Signal= 85.0% baseline
  [Fatigue] [WARN] WARNING
  [LED] Set to YELLOW (1023, 512, 0)
  [Motor] PULSE: 100ms @ 800/1023 intensity (WARN)
```

---

### **Case 3: 모터 제어만 테스트**
```python
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = True
ENABLE_LED = False
ENABLE_OLED = False

DEBUG_MOTOR_CONTROL = True
DEBUG_INTERVAL_CYCLES = 1
```

**출력 예시:**
```
[Cycle 1]
  [EMG] RMS= 2010.5 | Signal=100.0% baseline
  [Fatigue] [OK] NORMAL
  [Motor] OFF (normal)

[Cycle 8]
  [EMG] RMS= 1300.2 | Signal= 65.0% baseline
  [Fatigue] [CRIT] CRITICAL
  [Motor] CONTINUOUS: 300ms @ 1000/1023 intensity (CRIT)
```

---

### **Case 4: OLED만 테스트**
```python
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = False
ENABLE_LED = False
ENABLE_OLED = True

DEBUG_OLED_UPDATES = True
DEBUG_INTERVAL_CYCLES = 1
```

**출력 예시:**
```
[Cycle 1]
  [EMG] RMS= 2010.5 | Signal=100.0% baseline
  [Fatigue] [OK] NORMAL
  [OLED] Update: Fatigue=100.0%, Status=normal

[Cycle 2]
  [EMG] RMS= 2015.3 | Signal=100.2% baseline
  [Fatigue] [OK] NORMAL
  [OLED] Update: Fatigue=100.2%, Status=normal
```

---

### **Case 5: 전체 시스템 (기본)**
```python
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = True
ENABLE_LED = True
ENABLE_OLED = True

DEBUG_EMG_VALUES = True
DEBUG_LED_CONTROL = True
DEBUG_MOTOR_CONTROL = True
DEBUG_OLED_UPDATES = True
DEBUG_INTERVAL_CYCLES = 1
```

**출력 예시:**
```
[Cycle 1]
  [EMG] RMS= 2010.5 | Signal=100.0% baseline
  [Fatigue] [OK] NORMAL
  [LED] Set to GREEN (0, 1023, 0)
  [Motor] OFF (normal)
  [OLED] Update: Fatigue=100.0%, Status=normal
```

---

## 🔍 **DEBUG_INTERVAL_CYCLES 설명**

매 몇 사이클마다 출력할지 제어:

```python
DEBUG_INTERVAL_CYCLES = 1   # 매번 출력 (초당 1회)
DEBUG_INTERVAL_CYCLES = 5   # 5번마다 출력 (초당 0.2회)
DEBUG_INTERVAL_CYCLES = 10  # 10번마다 출력 (초당 0.1회)
```

**권장:**
- 빠른 테스트: `1` (매번)
- 장시간 모니터링: `10` (로그 양 감소)

---

## 🚀 **실제 사용법**

### **Step 1: config.py 수정**
```python
# firmware/config.py
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_LED = True
ENABLE_MOTOR = False  # 모터 비활성화 (테스트 중 안전)
ENABLE_OLED = False   # OLED 비활성화

DEBUG_EMG_VALUES = True
DEBUG_LED_CONTROL = True
```

### **Step 2: ESP32에 업로드**
Thonny에서:
- `config.py` → `/config.py` (덮어쓰기)
- `main.py` → `/main.py` (덮어쓰기)

### **Step 3: 실행**
```
F5 또는 >>> exec(open('main.py').read())
```

### **Step 4: 로그 확인**
```
[Init] Initializing hardware...
[Init] DEBUG mode: EMG=True, Motor=False, LED=True, OLED=False
[Init] EMG sensor... OK
[Init] Vibration motor... DISABLED
[Init] RGB LED... OK
[Init] OLED display... DISABLED

[Calib] Entering calibration in 3 seconds...
```

---

## 📊 **DEBUG OFF 모드 (배포용)**

디버그 없이 간단한 로그만:
```python
DEBUG = False
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = True
ENABLE_LED = True
ENABLE_OLED = True

# DEBUG_* 옵션들은 무시됨
```

**출력 예시 (간결함):**
```
[  10s] OK   | RMS= 2010.5 | Signal=100.0%
[  20s] OK   | RMS= 2015.3 | Signal=100.2%
[  30s] WARN | RMS= 1700.1 | Signal= 85.0%
[  40s] CRIT | RMS= 1300.2 | Signal= 65.0%
```

---

## 🎯 **문제 해결 체크리스트**

### EMG 센서 문제?
```python
DEBUG = True
ENABLE_EMG_SENSOR = True
ENABLE_MOTOR = False
ENABLE_LED = False
ENABLE_OLED = False

DEBUG_EMG_VALUES = True
DEBUG_INTERVAL_CYCLES = 1
```
→ RMS 값이 안정적인지 확인 (범위: 1500~2500)

### LED 제어 안 됨?
```python
ENABLE_LED = True
DEBUG_LED_CONTROL = True
```
→ 로그에 "Set to GREEN/YELLOW/RED" 출력되는지 확인

### 모터 작동 확인?
```python
ENABLE_MOTOR = True
DEBUG_MOTOR_CONTROL = True
```
→ 로그에 "PULSE" 또는 "CONTINUOUS" 출력되는지 확인

### OLED 화면 안 나옴?
```python
ENABLE_OLED = True
DEBUG_OLED_UPDATES = True
```
→ I2C 연결 확인, 주소 0x3C 맞는지 확인

---

## 💡 **팁**

1. **한 번에 한 장치씩 테스트**하기
   - 한 번에 모든 장치를 enable하면 문제 원인 파악 어려움

2. **로그가 너무 많으면** `DEBUG_INTERVAL_CYCLES` 증가
   - 터미널 버퍼 오버플로우 방지

3. **특정 상황만 확인할 때** 해당 플래그만 True
   ```python
   DEBUG_EMG_VALUES = True
   DEBUG_LED_CONTROL = False
   DEBUG_MOTOR_CONTROL = False
   DEBUG_OLED_UPDATES = False
   ```

