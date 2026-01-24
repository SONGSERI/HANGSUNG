# Raw Data Parsing Structure

본 문서는 SMT 설비 Raw 운전 데이터를 분석용 DB 구조로 적재하기 위한  
파싱 기준, 구조, 처리 흐름을 정의한다.

본 Raw 데이터는 이벤트 로그가 아닌 **설비 운전 결과 요약 데이터**이며,  
분석 이전에 해석·구조화 단계가 필요하다.

---

## 1. Raw 데이터 구조 개요

Raw 데이터는 다음과 같은 섹션 기반 구조를 가진다.

- 제품정보  
- 설비정보 (Time)  
- 설비 및 생산 정보 (Count)

각 Raw 데이터 1건은 **특정 Lot을 특정 설비가 일정 기간 운전한 결과 요약**을 의미한다.

---

## 2. 파싱 기본 단위

파싱의 기본 단위는 다음과 같다.

- **1 Raw Data = 1 Lot × 1 Machine × 1 Run 요약**

이를 기준으로 DB는 Lot 단위와 설비 Run 단위로 분리하여 구성한다.

---

## 3. 식별 기준 (Identification Keys)

### Lot 식별 기준
- ProductID  
- Rev  
- Stage  
- Lane  
- LotName / LotNumber  
- PlanID  

→ LOT 테이블의 논리적 식별 기준

### Run 식별 기준
- Lot 식별 정보  
- Machine ID (파일명 또는 외부 메타정보)  
- Raw 데이터 수집 시각  

→ MACHINE_RUN 테이블 식별 기준

---

## 4. 테이블별 파싱 구조

### 4.1 LOT

**대상 영역**
- 제품정보

**파싱 항목**
- Stage  
- Lane  
- ProductID  
- Rev  
- PlanID  
- Output  
- LotName  
- LotNumber  
- LotBoard  
- LotModule  

**파싱 원칙**
- Lot 단위 고정 정보
- 동일 Lot 재수집 시 Upsert 대상

---

### 4.2 MACHINE_RUN

**의미**
- Lot 기준 설비 1회 운전 요약 단위

**생성 규칙**
- Raw 데이터 1건당 1건 생성
- LOT 파싱 이후 생성

**주요 항목**
- lot_id  
- machine_id  
- stage_no  
- lane_no  
- collect_time  

---

### 4.3 MACHINE_TIME_SUMMARY

**대상 영역**
- 설비정보 (Time)

**파싱 항목**
- PowerON  
- Prod  
- Actual  
- Idle  
- Load  
- BRcg  
- Mount  
- TotalStop  
- Fwait  
- Rwait  
- Pwait  
- McFwait  

**파싱 원칙**
- 누적 시간 값 그대로 저장
- 단위: second
- 계산 및 비율 산출은 분석 단계에서 수행

---

### 4.4 MACHINE_STOP_SUMMARY

**대상 영역**
- 설비정보 (Time) 중 Stop 계열 항목
- 설비 및 생산 정보 (Count) 중 Stop Count

**파싱 항목**
- SCStop  
- CPErr  
- CRErr  
- PRDStop  
- 기타 Stop 관련 항목

**파싱 원칙**
- Stop 원인별 시간(sec)과 횟수(count) 분리 저장
- Time 영역 → *_sec  
- Count 영역 → *_cnt  

---

### 4.5 PRODUCTION_QUALITY_SUMMARY

**대상 영역**
- 설비 및 생산 정보 (Count)

**파싱 항목**
- Board  
- Module  
- TPickup  
- TMount  
- TPMiss  
- TRMiss  

**파싱 원칙**
- 생산 및 품질 결과 지표
- 불량률, PPM, 효율 분석의 기준 데이터

---

## 5. 파싱 처리 흐름

1. Raw 데이터 수신  
2. 섹션 분리 (제품정보 / Time / Count)  
3. LOT 파싱 및 Upsert  
4. MACHINE_RUN 생성  
5. MACHINE_TIME_SUMMARY 적재  
6. MACHINE_STOP_SUMMARY 적재  
7. PRODUCTION_QUALITY_SUMMARY 적재  

---

## 6. 설계 의도

- Lot / Run 분리를 통한 재수집 대응
- Time / Count 분리를 통한 의미 혼선 방지
- 누적 원본 데이터 보존으로 재분석 가능 구조 확보
- 분석 과제 확정 이전 단계의 데이터 구조화 목적

---

## 7. 요약

본 Raw 데이터는 설비 운전 결과 요약 데이터이며,  
Lot × 설비 Run 단위를 기준으로 섹션별 파싱 후  
정규화된 분석용 테이블로 적재한다.
