<SmartSpec_Document>
## 1. Goal
- 사용자가 설정한 **신호 주기(Signal Duration)**에 따른 교차로 효율성을 측정하는 Tkinter 기반 시뮬레이터 개발.
- 특정 차량 대수를 모두 통과시키는 데 발생하는 **'총 대기 시간 합계(Total Wait Time)'**와 **'전체 소요 시간'**을 측정하여, 어떤 주기가 가장 경제적인지 분석하는 실험 환경 구축.

## 2. Tech Stack
- **Language:** Python 3.10+
- **Library:** Tkinter (Canvas), Math (물리 계산)
- **Architecture:** OOP 기반 (Vehicle 객체가 자신의 상태와 대기 시간을 직접 관리)

## 3. Core Logic & Features (Integrated)
- **Vehicle Behavior & Safety:**
  - **직진 전용:** 모든 차량은 교차로에서 오직 직진만 수행함.
  - **정지선(Stop Line):** 4개 차로 전체 폭에 걸쳐 명확한 노란색 정지선을 구현.
  - **추돌 방지(Gap Control):** 앞차와의 안전거리를 실시간 계산하여 정지/출발을 결정. 신호가 바뀌어도 앞차가 있으면 출발하지 않음.
- **Dynamic Control System:**
  - **Time Scale (0.5x~5.0x):** 슬라이더로 조절. 차량 속도는 배율에 비례, 신호 타이머는 배율에 반비례하여 동기화.
  - **Custom Signal (5s~30s):** 사용자가 슬라이더로 주기를 설정. 시뮬레이션 시작 시 설정값을 잠금(Lock) 처리하여 데이터 오염 방지.
  - **Termination Condition:** 목표 차량 수(100~1000대) 통과 시 즉시 자동 정지.
- **Data Analytics:**
  - **Metric 1:** 총 대기 시간 합계 (모든 차량의 정지 시간 ms 단위 누적 후 초 단위 변환).
  - **Metric 2:** 전체 시뮬레이션 소요 시간 (시작부터 목표 대수 통과까지).
  - **Export:** 종료 시 결과를 `traffic_results.csv`에 자동 저장하고 요약 리포트 창 출력.

## 4. Implementation Tasks (Step-by-Step)
- **Step 1 [Layout & UI]:** 4지 교차로 맵 디자인. 사이드바에 신호 주기, 목표 차량 수, 시간 배율 슬라이더와 재생/정지 버튼 배치.
- **Step 2 [Initialization Logic]:** UI 변수를 먼저 선언한 후 엔진 객체를 생성하여, 슬라이더의 초기값이 엔진 설정과 완벽히 동기화되도록 설계.
- **Step 3 [Physics Engine]:** `root.after()` 기반의 메인 루프 구축. 차량 객체가 신호등과 앞차를 감지하여 상태(Moving/Waiting)를 전환하고 대기 시간을 기록.
- **Step 4 [Reporting]:** 시뮬레이션 완료 시 데이터 시각화 및 CSV 저장 기능 구현.

## 5. 3-Level Boundaries
✅ **Always do:**
- 모든 Python 파일 최상단에 주석으로 파일 이름 기재.
- 대기 시간 단위를 '초(Seconds)'로 통일하여 신호 주기와 비교 가능하게 할 것.
- 시뮬레이션 일시정지(Pause) 시 모든 물리 연산과 타이머를 중단할 것.

⚠️ **Ask first:**
- 시뮬레이션 종료 후 즉시 새로운 실험을 위해 환경을 초기화(Reset)할지 여부 문의.
- 차량 유입 빈도(Spawn Rate)의 기본값 설정 범위를 문의.

🚫 **Never do:**
- `time.sleep()` 사용 절대 금지 (GUI 프리징 방지).
- 차량이 정지선을 무시하거나 다른 객체와 겹치는 현상(Overlap) 방지.
- 외부 이미지 파일 사용 금지 (오직 Canvas 도형만 활용).

## 6. Quality Assurance (Self-Check)
- [ ] 시간 배율을 조절할 때 차량 속도와 신호등 텀이 의도한 비율대로 변하는가?
- [ ] 정지선 앞에서 차량들이 추돌 없이 차례대로 대기하며 대기 시간이 누적되는가?
- [ ] 목표 대수 통과 시 정확히 시뮬레이션이 멈추고 결과 리포트가 생성되는가?
- [ ] 모든 데이터가 `traffic_results.csv`에 정확한 헤더와 함께 저장되는가?

## 7. 변경사항
- **[2026-03-18] 차량 유입 빈도(Spawn Rate) 제어 기능 추가:**
  - 기존 하드코딩된 차량 생성 확률(0.04)을 사용자가 조절 가능한 변수로 추상화.
  - UI에 '스폰 배율(Spawn Multiplier)' 슬라이더 추가 (범위: 1.0x ~ 10.0x).
  - 기본값을 4.0x(내부 확률 0.02)로 설정하여 초기 교통량 최적화.
  - 시뮬레이션 중 데이터 오염 방지를 위해 신호 주기 슬라이더와 함께 잠금(Lock) 기능 적용.
</SmartSpec_Document>