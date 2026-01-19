

# SMT ProductReport 로그 파싱 규칙

## 1. 목적

본 문서는 Panasonic SMT 설비에서 생성되는
**ProductReport 로그 파일**을 파싱하여
DB(LOT 중심 ERD)에 적재하기 위한 규칙을 정의한다.

---

## 2. 기본 원칙

* 로그 파일 1개 = LOT 1개
* LOT 단위로 모든 데이터 수집
* `[Section]` 단위로 파싱
* Key=Value 형식 사용
* 문자열 값

  * 앞뒤 따옴표 제거
* 숫자 값

  * 정수 → int
  * 소수 → float
* 값이 없는 경우

  * NULL 허용
* 계산 컬럼은

  * **DB 저장 후 후처리 계산**

---

## 3. 파일명 파싱 규칙

### 3.1 파일명 형식

```
[Timestamp]-[Machine]-[Stage]-[Lane]-[Head]-[LotName].[Ext]
```

예시

```
20260116000000391-05-1-1-3-NAD_H_T_EBR37416101.u01
```

### 3.2 파싱 항목

| 위치  | 항목        | 설명          |
| --- | --------- | ----------- |
| 1   | Timestamp | 로그 생성 시각    |
| 2   | Machine   | 설비 번호       |
| 3   | Stage     | Stage 번호    |
| 4   | Lane      | Lane 번호     |
| 5   | Head      | Head 그룹     |
| 6   | LotName   | LOT 이름      |
| 확장자 | Ext       | 로그 타입 (u01) |

### 3.3 적용 컬럼

* LOT.machine
* LOT.stage_no
* LOT.lane_no
* LOT.lot_name

---

## 4. Section 공통 파싱 규칙

* `[SectionName]` 으로 시작
* 다음 `[Section]` 나오기 전까지 해당 영역
* 데이터 타입

| 타입        | 처리         |
| --------- | ---------- |
| Key=Value | 컬럼 매핑      |
| "문자열"     | 따옴표 제거     |
| 공백 구분     | 테이블 형태 데이터 |

---

## 5. [Index] 파싱

### 주요 항목

| 로그 키    | DB 컬럼           |
| ------- | --------------- |
| Format  | LOT.log_type    |
| Machine | LOT.machine     |
| Date    | LOT.report_date |
| MJSID   | LOT.mjs_id      |

---

## 6. [Information] 파싱

### 주요 항목

| 로그 키      | DB 컬럼          |
| --------- | -------------- |
| Stage     | LOT.stage_no   |
| Lane      | LOT.lane_no    |
| ProductID | LOT.product_id |
| Rev       | LOT.rev        |
| PlanID    | LOT.plan_id    |
| LotName   | LOT.lot_name   |
| Output    | LOT.output_qty |

---

## 7. [Time] 파싱

### 대상 테이블

* TIME_METRIC

### 파싱 방식

* Key=Value 전부 컬럼 매핑

| 로그 키      | DB 컬럼           |
| --------- | --------------- |
| PowerON   | power_on_time   |
| Change    | change_time     |
| Idle      | idle_time       |
| Prod      | prod_time       |
| Actual    | actual_time     |
| Load      | load_time       |
| Mount     | mount_time      |
| TotalStop | total_stop_time |
| ...       | 동일 이름 매핑        |

> 주의
> 로그 키와 컬럼명은
> **Snake Case 변환 후 저장**

---

## 8. [CycleTime] 파싱

### 대상 테이블

* CYCLE_STAT

| 로그 키   | DB 컬럼        |
| ------ | ------------ |
| CTime1 | cycle_time_1 |
| CTime2 | cycle_time_2 |
| CTime3 | cycle_time_3 |

---

## 9. [Count] 파싱

### 대상 테이블

* COUNT_METRIC

| 로그 키    | DB 컬럼            |
| ------- | ---------------- |
| Board   | board_cnt        |
| Module  | module_cnt       |
| TPickup | total_pickup_cnt |
| TPMiss  | pickup_miss_cnt  |
| TRMiss  | retry_miss_cnt   |
| TMount  | total_mount_cnt  |
| ...     | 동일 이름 매핑         |

---

## 10. [MountPickupFeeder] 파싱

### 대상 테이블

* RESOURCE_METRIC

### 파싱 방식

* 첫 줄 → 헤더
* 이후 한 줄 = 1 Row

### 주요 매핑

| 위치        | 컬럼              |
| --------- | --------------- |
| BLKSerial | resource_serial |
| PartsName | part_no         |
| Pickup    | pickup_cnt      |
| PMiss     | p_miss_cnt      |
| RMiss     | r_miss_cnt      |
| DMiss     | d_miss_cnt      |
| MMiss     | m_miss_cnt      |
| HMiss     | h_miss_cnt      |
| TRSMiss   | trs_miss_cnt    |
| Mount     | mount_cnt       |

* resource_type = `FEEDER`

---

## 11. [MountPickupNozzle] 파싱

### 대상 테이블

* RESOURCE_METRIC

### 주요 매핑

| 로그 위치  | 컬럼         |
| ------ | ---------- |
| Head   | head_no    |
| NCAdd  | nozzle_no  |
| Pickup | pickup_cnt |
| PMiss  | p_miss_cnt |
| Mount  | mount_cnt  |

* resource_type = `NOZZLE`

---

## 12. [InspectionData] 파싱

### 대상 테이블

* QUALITY_SUMMARY

| 로그 키       | DB 컬럼           |
| ---------- | --------------- |
| BadBoard   | bad_board_cnt   |
| BadBlock   | bad_block_cnt   |
| BadParts   | bad_parts_cnt   |
| OKParts    | ok_parts_cnt    |
| RetryBoard | retry_board_cnt |
| ...        | 동일 이름 매핑        |

---

## 13. 계산 컬럼 처리 규칙

### TIME_METRIC

```
run_ratio   = prod_time / power_on_time
stop_ratio  = total_stop_time / power_on_time
mount_ratio = mount_time / prod_time
idle_ratio  = idle_time / power_on_time
```

---

### COUNT_METRIC

```
pickup_miss_rate = pickup_miss_cnt / total_pickup_cnt
mount_yield      = total_mount_cnt / total_pickup_cnt
retry_rate       = retry_miss_cnt / total_pickup_cnt
```

---

### CYCLE_STAT

```
cycle_avg = (ct1 + ct2 + ct3) / 3
cycle_std = STD(ct1, ct2, ct3)
```

---

### RESOURCE_METRIC

```
total_error_cnt =
p_miss + r_miss + d_miss + m_miss + h_miss + trs_miss

miss_rate =
total_error_cnt / pickup_cnt

efficiency =
mount_cnt / pickup_cnt
```

---

### QUALITY_SUMMARY

```
board_yield =
1 - (bad_board_cnt / lot_block_cnt)

part_yield =
ok_parts_cnt / (ok_parts_cnt + bad_parts_cnt)

retry_ratio =
retry_board_cnt / lot_block_cnt
```

---

## 14. 예외 처리

* pickup_cnt = 0
  → 분모 0 계산 금지
* 문자열 컬럼 NULL 허용
* 숫자 필드 파싱 실패 시
  → NULL 저장

---

## 15. 요약

* 로그 원본 값은 그대로 적재
* 분석 값은 후처리 계산
* 모든 하위 테이블은
  LOT.lot_name 기준 FK 연결
* 파서 변경 없이
  로그 포맷 확장 가능

---

