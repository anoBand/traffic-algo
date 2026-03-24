# 📝 [Smart Spec] Traffic Efficiency Simulator: Phase-by-Phase Development

## 🎯 Goal
4지 교차로에서 신호 대기 시간(`duration`) 변화에 따른 효율성을 객체 기반 시뮬레이션으로 측정합니다. `terminal_runner`를 통해 현실적인 교통 부하 상황에서의 통계적 유의성을 확보한 뒤, GUI를 통해 시각적으로 검증하는 워크플로우를 가집니다.

## 📊 Realistic Scenario Standards (현실적 변수 범위)
모든 Phase의 검증은 다음의 현실 기반 범위를 포함해야 합니다.

| 수준 | Spawn Rate (차량 생성 밀도) | 비고 (현실 환산 시) |
| :--- | :--- | :--- |
| **Low** | `0.02` | 한산한 도로 (약 360 VPH) |
| **Medium** | `0.04` | 일반 시내 도로 (약 720 VPH) |
| **High** | `0.06` | 혼잡 구간 (약 1,080 VPH) |
| **Saturated** | `0.08` | 포화 상태 (약 1,440 VPH) |

*   **Duration Range:** `20s ~ 100s` (국내 신호 설계 지침 기준)
*   **Target Count:** 최소 `500 ~ 1,000`대 (통계적 안정성 확보)

## 🔄 Phase Roadmap (Iterative Development)
**에이전트는 사용자의 승인 전까지 현재 페이즈에만 집중합니다.**

* **Phase A: Straight Only (Current)**
    * 북-남 / 동-서 직진 신호 체계 구축.
    * `logic.py` 핵심 엔진 구현: 1s 반응 지연 로직 포함.
    * **Verification:** 현실적 범위(20-100s)에서의 대기 시간 Baseline 측정.
* **Phase B: Left Turn Included**
    * 좌회전 전용 차선 및 신호 페이즈 추가.
    * **Verification:** 좌회전 추가 시 최적 Duration이 우측으로 이동하는지(U자 곡선) 확인.
* **Phase C: Pedestrians & Crosswalks**
    * 보행자 객체 및 보행 신호 추가. 차량-보행자 간 상호작용 반영.
* **Phase D: Scramble (Diagonal)**
    * 모든 차량 정지 후 보행자만 전 방향 이동하는 페이즈 추가.

## 🏃 Implementation Task (Current: Phase A)
1.  **Engine Development (`logic.py`):**
    * `Vehicle` 클래스: 좌표, 속도, 대기 시간 상태 관리.
    * **1s Delay:** 정지선 맨 앞 차량은 신호 변경 후 1.0초(시뮬레이션 타임 기준) 뒤에 가속 시작.
    * **Color Coding:** 대기 시간에 따라 Green -> Yellow -> Red 가시화.
2.  **Data Logging (`terminal_runner.py`):**
    * **Realistic Survey:** `spawn_rate`(0.02~0.08)별로 `duration`(20~100) 이중 루프 실행.
    * **정확도 확보:** 동일 조건 시나리오를 **각 3~5회 반복 실행**하여 평균값 기록.
3.  **Interface (`main.py`):**
    * Tkinter Canvas 기반 교차로 렌더링 및 실시간 파라미터 제어.

## ⚠️ 3-Level Boundaries (경계 시스템)

✅ **Always do:**
- 모든 파일 최상단에 `# filename.py` 주석 작성.
- `logic.py`는 UI 라이브러리에 의존하지 않는 순순 연산 모듈로 유지.
- 새로운 페이즈 구현 후 반드시 **현실적 변수 범위**에서 `terminal_runner`를 실행하여 효율 변화를 리포트.
- 차량의 '평균 대기 시간' 산출 시, 교차로 진입 대기부터 통과 완료 시점까지의 시간을 정확히 계산.

⚠️ **Ask first:**
- 특정 페이즈에서 대기 시간이 급격히 증가하여 시뮬레이션이 종료되지 않을 경우.
- 새로운 외부 라이브러리 설치가 필요할 경우.

🚫 **Never do:**
- 사용자의 지시 없이 다음 페이즈 기능을 미리 구현하지 말 것.
- `time_scale` 조절 시 물리 연산(충돌/정지선 체크)을 건너뛰지 말 것.
