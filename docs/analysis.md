# ERD 기반 데이터 분석 정리

본 문서는 `parser/docs/erd_diagram.mmd`에 정의된 엔티티를 기준으로, 
현재 구조에서 바로 수행 가능한 분석 주제와 지표를 정리한 내용이다.

## 1) 분석 프레임 (문제 정의 흐름)

1. **무엇이 문제인가?** → 정지/에러 유형 식별 (`STOP_LOG`, `PICKUP_ERROR_SUMMARY`)
2. **어디서 문제인가?** → 라인/스테이지/설비/Lot 구간 식별 (`MACHINE`, `LOT_MACHINE`, `FILE`)
3. **어떤 패턴인가?** → 자주 발생(빈도) vs 오래 지속(시간) 구분 (`stop_count`, `duration_sec`)
4. **영향은 얼마나 큰가?** → 생산시간 손실, 품질 저하, 병목 영향 추정 (`MACHINE_TIME_SUMMARY`)
5. **무엇을 할 것인가?** → 우선순위 과제(설비, 부품, 태그, 운영 표준) 도출

---

## 2) ERD 기준 핵심 분석 도메인

## A. 운영시간/가동효율 분석

### 사용 테이블
- `MACHINE_TIME_SUMMARY`
- `LOT_MACHINE`, `LOT`, `MACHINE`

### 핵심 지표
- 가동률(운영 관점): `running_time_sec / power_on_time_sec`
- 순생산률(실생산 관점): `real_running_time_sec / power_on_time_sec`
- 정지손실률: `total_stop_time_sec / power_on_time_sec`
- 공정별 시간비중: `transfer`, `recognition`, `placement` 시간 비율

### 대표 분석 질문
- 동일 라인에서 어떤 설비(Stage/Machine)가 평균 가동률이 낮은가?
- Lot별 성능 편차가 큰 설비는 어디인가?
- 실장시간 대비 인식/이송 비중이 비정상적으로 높은 구간은 어디인가?

### 기대 액션
- 저효율 설비 우선 점검 리스트
- 시간 손실 원인별(이송/인식/실장) 개선 과제 분리

---

## B. 정지(Stop) 원인 분석

### 사용 테이블
- `STOP_LOG`, `STOP_REASON`
- `LOT_MACHINE`, `MACHINE`, `LOT`

### 핵심 지표
- 정지 빈도: `sum(stop_count)`
- 정지 시간: `sum(duration_sec)`
- 건당 평균 정지시간: `sum(duration_sec) / sum(stop_count)`
- 정지그룹 비중: `WAIT/ERROR/QUALITY/SETUP` 별 시간·횟수 점유율

### 대표 분석 질문
- “자주 멈추는 원인”과 “오래 멈추는 원인”은 각각 무엇인가?
- 동일한 정지코드가 특정 설비/스테이지에 편중되는가?
- Lot 시작/종료 구간에서 특정 정지코드가 집중되는가?

### 기대 액션
- Top N 정지코드 개선 우선순위
- 정지코드별 표준 대응시간(SLA) 기준 수립

---

## C. 품질/에러 분석 (설비 단위)

### 사용 테이블
- `PICKUP_ERROR_SUMMARY`
- `LOT_MACHINE`, `MACHINE`

### 핵심 지표
- 총 에러율: `total_error_count / total_pickup_count`
- 유형별 에러율:
  - `pickup_error_count / total_pickup_count`
  - `recognition_error_count / total_pickup_count`
  - `placement_error_count / total_pickup_count`
  - 기타 유형별 동일 방식

### 대표 분석 질문
- 어떤 설비가 평균 대비 품질 에러율이 높은가?
- 동일 설비에서 Lot별 에러율 급등 구간이 있는가?
- 정지시간이 긴 설비와 에러율 높은 설비가 겹치는가?

### 기대 액션
- 품질 취약 설비의 유지보수/보정 주기 최적화
- 에러 유형별 점검 체크리스트 개선

---

## D. 부품/피더/노즐 관점 분석

### 사용 테이블
- `COMPONENT`, `COMPONENT_PICKUP_SUMMARY`
- `MACHINE`, `LOT_MACHINE`

### 핵심 지표
- 부품별 에러율: `error_count / pickup_count`
- 인식 에러율: `recognition_error_count / pickup_count`
- 픽업 에러율: `pickup_error_count / pickup_count`

### 대표 분석 질문
- 특정 `part_number` 또는 `feeder_serial`이 고에러를 유발하는가?
- 특정 노즐(`nozzle_serial`, `holder`) 조합에서 에러가 집중되는가?
- 설비가 달라도 동일 부품에서 반복되는 문제인가?

### 기대 액션
- 고위험 부품/피더/노즐 교체 우선순위 제시
- 부품-설비 매칭 최적화 가이드

---

## E. 태그/실시간 데이터 기반 이상탐지

### 사용 테이블
- `TAG_INFO`, `TAG_SPEC`, `TAG_REALTIME`, `TAG_CATEGORY`
- (선택) `BEINGPLUS_INGEST_QUEUE`, `BEINGPLUS_PROC_LOG`

### 핵심 지표
- 스펙 이탈률: `out_of_spec_count / total_count`
- 이탈 지속시간: 연속 이탈 구간 길이
- 설비별 태그 안정성: 변동성(표준편차), 급변 이벤트 빈도
- 수집 안정성: 큐 적체량, 재시도율, 전송 실패율

### 대표 분석 질문
- 어떤 태그가 불량/정지 이벤트 이전에 선행 이상 신호를 보이는가?
- 설비별로 동일 태그의 기준값 이탈 패턴이 다른가?
- 데이터 수집 지연/실패가 특정 시간대나 설비에서 증가하는가?

### 기대 액션
- 조기경보(early warning) 태그 후보 선정
- 기준값(TARGET/LCL/UCL) 재튜닝 대상 도출

---

## 3) 통합 관점의 우선 분석 시나리오

### 시나리오 1: 정지 손실 개선
1. `STOP_LOG`에서 시간손실 Top 정지코드 선정
2. 해당 코드가 집중된 `MACHINE`/`LOT` 식별
3. 동일 구간의 `MACHINE_TIME_SUMMARY`로 손실시간/가동률 영향 계산
4. 개선 전후 KPI 추적

### 시나리오 2: 품질-설비 연계 개선
1. `PICKUP_ERROR_SUMMARY`로 고에러 설비 탐지
2. `COMPONENT_PICKUP_SUMMARY`로 원인 부품/노즐 후보 압축
3. 관련 정지코드(`QUALITY`, `ERROR`) 동시 발생 여부 확인
4. 설비/부품 조합별 액션 도출

### 시나리오 3: 태그 기반 선제 대응
1. 불량/정지 직전 구간의 `TAG_REALTIME` 패턴 수집
2. `TAG_SPEC` 기준 이탈 및 급변 특성 계산
3. 실제 이벤트(`STOP_LOG`, `PICKUP_ERROR_SUMMARY`)와 선행성 검증
4. 알람 룰 또는 예측모델 입력 변수 선정

---

## 4) 대시보드 권장 구성

- **경영 요약**: 가동률, 정지손실률, 에러율, Top 손실 요인
- **설비 관점**: Line/Stage/Machine Drill-down
- **정지 분석**: 코드/그룹/시간대 Heatmap
- **품질 분석**: 에러 유형 Pareto, Lot 추이
- **부품 분석**: Part/Feeder/Nozzle 위험도 순위
- **태그 분석**: 스펙 이탈 모니터링, 수집 파이프라인 상태

---

## 5) 데이터 품질 점검 체크리스트

- `FILE` ↔ `LOT_MACHINE` 매핑 누락 여부
- `STOP_REASON` 미정의 코드 존재 여부
- `pickup_count = 0` 인데 에러가 기록된 케이스
- `power_on_time_sec < running_time_sec` 같은 비정상 시간관계
- 태그 시계열의 중복 타임스탬프/결측 구간
- 수집 큐(`BEINGPLUS_INGEST_QUEUE`) 장기 `FAILED`/`PENDING` 적체

---
