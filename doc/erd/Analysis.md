
## 1. 현재 데이터(EXIST 컬럼)로 가능한 분석

### 1.1 LOT 단위 생산성 분석 (기본)

사용 테이블

* LOT
* LOT_TIME_SUMMARY
* LOT_COUNT_SUMMARY

분석 항목

* LOT별 총 생산 시간 분해

  * prod_time / idle_time / stop_time / mount_time / actual_time 비율
* LOT별 생산량 분석

  * board_count, module_count, mount_count
* LOT별 생산성 지표

  * UPH = mount_count / actual_time
* LOT별 이상 LOT 탐지

  * 동일 Product 대비 actual_time 급증 LOT

---

### 1.2 설비 / Stage / Lane 비교 분석

사용 테이블

* LOT
* LOT_TIME_SUMMARY

분석 항목

* Machine 별 평균 생산 시간
* Stage 별 생산 편차
* Lane (Front / Rear) 성능 비교
* 동일 LOT Name 기준 Lane 편차 분석

의미

* 설비 밸런싱 문제 탐지
* 특정 Lane 병목 식별

---

### 1.3 자원(Resource) 기반 분석 (핵심)

사용 테이블

* LOT_RESOURCE_USAGE

분석 항목

* Feeder / Nozzle 별 Miss Rate
* Pickup 대비 Mount 효율
* 자원별 사용 빈도 TOP N
* 특정 LOT에서 집중적으로 실패한 자원 탐지
* Head / Lane 기준 자원 편중 분석

의미

* **현장 Trouble Shooting 1차 포인트**
* 노즐·피더 교체 근거 데이터 확보

---

### 1.4 제품(Product) 기준 비교 분석

사용 테이블

* LOT

분석 항목

* Product별 평균 생산 시간
* Product별 생산량 / 생산성
* Product별 자원 구성 차이

제약

* BOM 없음 → 원인 추적은 제한적

---

## 2. 확장 컬럼(NEW) 채워질 경우 가능한 분석

### 2.1 OEE 기반 분석

추가 컬럼

* planned_time
* availability_rate
* performance_rate
* oee_lite

분석 항목

* LOT / 설비 / Lane 기준 OEE Trend
* 계획 대비 실적 분석
* Shift / Line 단위 OEE 비교

---

### 2.2 Stop 원인 분석 (중요)

사용 테이블

* LOT_STOP_EVENT

분석 항목

* Stop Category 별 시간 분해
* Stop Code TOP 분석
* 반복 Stop 원인 식별
* 특정 자원 연관 Stop 분석

확장 포인트

* Alarm / Event 로그 연계

---

### 2.3 품질 / 수율 분석

추가 컬럼

* good_count
* reject_count
* yield_rate
* error_code / error_type

분석 항목

* LOT 수율 Trend
* 자원별 불량 기여도
* Product × Resource 불량 매트릭스

---

### 2.4 이상 탐지 / AI 분석

기반 데이터

* LOT_TIME_SUMMARY
* LOT_COUNT_SUMMARY
* LOT_RESOURCE_USAGE

가능 분석

* 이상 LOT 자동 탐지
* 자원 고장 조기 감지
* 생산성 급락 패턴 학습
* Lane 불균형 패턴 탐지

AI 관점

* LOT = 1 Sample
* Time / Count / Resource = Feature Vector

---

## 3. 현재 구조의 한계 (명확히)

불가능한 것

* 실시간 Cycle 분석
* Placement 위치 기반 불량
* 공정 간 연계 분석

->* 로그 특성상 LOT 종료 집계 데이터

---

