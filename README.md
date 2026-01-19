

## 1. 개요

* 대상 설비
  - Panasonic SMT Chip Mounter (NPM 계열)

* 대상 로그
  - ProductReport 

* 원칙
 - LOG 파일 1개 = LOT 1개
 - LOT 기준으로 모든 데이터 수집
 - 로그는 LOT 종료 후 생성되는 집계 로그 (실시간 데이터 아님)
 
---

## 2. LOG 파싱 규칙

### 2.1 파일 이름 규칙

* Production Report 파일명 형식

  ```
  [Timestamp]-[Machine]-[Stage]-[Lane]-[Head]-[LotName].[LogType]
  ```

* 파일명 예시

  ```
  20260116000000391-05-1-1-3-NAD_H_T_EBR37416101.u01
  ```

* 파일명 항목 설명

  * Timestamp
    로그 생성 시각 (YYYYMMDD + 시퀀스)

  * Machine
    설비 번호 (Machine No)

  * Stage
    Stage 번호
    ※ Stage ID / Name 은 로그에 존재하지 않음

  * Lane
    Lane 번호

  * Head
    Head 그룹 또는 Lane Side 구분 값
    (Front / Rear / Both 구분 용도로 사용)

  * LotName
    LOT 이름 (DB LOT 테이블의 기준 키)

  * LogType
    로그 유형 (ProductReport = u01)

---

### 2.2 공통 파싱 규칙

* `[Section]` 단위로 로그 파싱
* Key=Value 형식 사용
* 문자열 필드

  * 양쪽 따옴표 제거 후 저장
* 숫자 필드

  * 정수: int
  * 소수 포함 값: float
* 파싱 실패 항목은 NULL 허용

---

### 2.3 Header / Summary 영역

대상 섹션

```
[Index]
[Information]
[Time]
[Count]
```

처리 방식

* LOG 파일 1개당 1회 파싱
* LOT 기준 집계 데이터
* 아래 테이블에 각각 1 Row 생성

생성 테이블

* LOT

  * LOT 기본 정보
  * LotName, ProductID, PlanID, Rev 등

* LOT_TIME_SUMMARY

  * [Time] 섹션 기반 시간 집계 데이터
  * Production / Idle / Stop / Mount / Actual Time 등

* LOT_COUNT_SUMMARY

  * [Count] 섹션 기반 수량 집계 데이터
  * Board / Module / Pickup / Mount / Miss Count 등

---

### 2.4 Feeder / Nozzle 영역

대상 섹션

```
[MountPickupFeeder]
[MountPickupNozzle]
```

처리 방식

* 데이터 라인 1줄 = DB Row 1개 생성
* LOT 기준 하위 상세 실적 데이터
* 자원(Resource) 단위 사용량 집계

생성 테이블

* LOT_RESOURCE_USAGE

공통 규칙

* 상위 LOT 과 LotName 으로 연결
* Resource Master 테이블은 별도로 두지 않음
* 로그에 등장한 자원을 그대로 사용

---

#### 2.4.1 MountPickupFeeder 파싱

* Resource Type
  FEEDER

* 주요 파싱 필드 예

  * Feeder Serial
  * Parts Name
  * Pickup Count
  * Mount Count
  * Pickup Miss / RMiss / DMiss 등

* 처리 결과

  * Feeder 1개당 1 Row 생성
  * LOT_RESOURCE_USAGE 테이블에 저장

---

#### 2.4.2 MountPickupNozzle 파싱

* Resource Type
  NOZZLE

* 주요 파싱 필드 예

  * Nozzle ID
  * Head / Nozzle Address
  * Pickup Count
  * Mount Count
  * Miss Count

* 처리 결과

  * Nozzle 1개당 1 Row 생성
  * LOT_RESOURCE_USAGE 테이블에 저장

---

## 3. 설계 기준 요약

* 본 로그는 실시간 설비 데이터가 아님
* LOT 종료 후 생성되는 집계 리포트 로그
* Machine / Stage / Lane / Head 정보는
  파일명 + Header 정보 기반 컨텍스트로 관리
* Stage / Lane ID 는 별도 관리하지 않음
* Resource(Feeder / Nozzle)는
  마스터 테이블 없이 실적 기준으로 일단 생성

---
