# SMT Log Parsing Rules (ERD 기준)

본 문서는 **SMT 설비 로그 파일(u01, u03)**을 파싱하여
사전에 정의된 **ERD의 테이블과 컬럼에 데이터를 적재하기 위한 공식 파싱 규칙서**이다.

이 문서는 **개발자 / 데이터엔지니어 / 분석 담당자**가 공통으로 이해할 수 있도록 작성되었다.

---

## 1. 전체 구조 개요

### 1.1 데이터 흐름

```
[파일명] ──▶ FILE (메타데이터)
              └─▶ LOT
              └─▶ MACHINE
                    └─▶ LOT_MACHINE
                            ├─▶ MACHINE_TIME_SUMMARY (u01)
                            ├─▶ STOP_LOG (u01)
                            ├─▶ PICKUP_ERROR_SUMMARY (u03)
                            └─▶ COMPONENT / COMPONENT_PICKUP_SUMMARY (u03)
```

### 1.2 핵심 원칙

* **ERD에 정의된 테이블/컬럼만 생성**
* 로그에 없는 정보는 **추정하거나 계산하지 않음**
* 모든 집계는 **Lot + Machine 단위**
* u01 = 시간/정지 정보
* u03 = 픽업/에러/부품 정보

---

## 2. 파일명 파싱 규칙 (FILE 테이블)

### 2.1 대상 파일

* 확장자: `.u01`, `.u03`

### 2.2 파일명 형식

```
YYYYMMDDNNNNNN-LINE-PROCESS-STAGE-MACHINE-LOTNAME.u01
```

### 2.3 FILE 테이블 컬럼 매핑

| 컬럼명           | 설명       | 파싱 규칙                |
| ------------- | -------- | -------------------- |
| file_id       | 파일 PK    | 시스템 생성               |
| file_name     | 원본 파일명   | 전체 문자열               |
| file_datetime | 기준 일자    | 파일명 앞 8자리 (YYYYMMDD) |
| file_sequence | 일자 내 시퀀스 | YYYYMMDD 뒤 숫자        |
| line_id       | 라인 ID    | 파일명 2번째 토큰           |
| process_no    | 공정 번호    | 파일명 3번째 토큰           |
| stage_no      | 스테이지 번호  | 파일명 4번째 토큰           |
| machine_order | 설비 번호    | 파일명 5번째 토큰           |
| lot_name      | Lot 이름   | 파일명 6번째 토큰           |
| file_type     | 로그 타입    | 확장자(u01 / u03)       |

> ⚠️ 파일명 규칙 불일치 시 해당 파일은 적재 대상에서 제외

---

## 3. LOT 테이블 파싱 규칙

### 3.1 생성 기준

* 동일 `lot_name` 최초 등장 시 1건 생성

| 컬럼명        | 설명      | 파싱 규칙                |
| ---------- | ------- | -------------------- |
| lot_id     | Lot PK  | hash(lot_name)       |
| lot_name   | Lot 이름  | FILE.lot_name        |
| start_time | Lot 시작  | u01 로그의 Lot Start 시각 |
| end_time   | Lot 종료  | u01 로그의 Lot End 시각   |
| lane       | Lane 정보 | 로그에 명시된 경우만          |

---

## 4. MACHINE 테이블 파싱 규칙

### 4.1 생성 기준

* 동일 `(line_id + stage_no + machine_order)` 최초 등장 시

| 컬럼명           | 설명    | 파싱 규칙                                    |
| ------------- | ----- | ---------------------------------------- |
| machine_id    | 설비 PK | hash(line_id + stage_no + machine_order) |
| line_id       | 라인    | FILE.line_id                             |
| stage_no      | 스테이지  | FILE.stage_no                            |
| machine_order | 설비 번호 | FILE.machine_order                       |

---

## 5. LOT_MACHINE 테이블 파싱 규칙

### 5.1 역할

* **Lot과 설비의 실제 작업 단위**

| 컬럼명            | 설명         | 파싱 규칙                     |
| -------------- | ---------- | ------------------------- |
| lot_machine_id | PK         | hash(lot_id + machine_id) |
| lot_id         | Lot FK     | LOT.lot_id                |
| machine_id     | Machine FK | MACHINE.machine_id        |

---

## 6. MACHINE_TIME_SUMMARY (u01)

### 6.1 대상

* u01 로그의 **Machine Time Summary 영역**

| 컬럼명                        | 설명    | 파싱 규칙                  |
| -------------------------- | ----- | ---------------------- |
| lot_machine_id             | FK    | LOT_MACHINE            |
| power_on_time_sec          | 전원 시간 | Power ON Time → 초      |
| running_time_sec           | 가동 시간 | Running Time           |
| real_running_time_sec      | 실가동   | Real Running Time      |
| total_stop_time_sec        | 총 정지  | Total Stop Time        |
| transfer_time_sec          | 이송    | Transfer Time          |
| board_recognition_time_sec | 인식    | Board Recognition Time |
| placement_time_sec         | 실장    | Placement Time         |

> 시간 값은 **로그 값을 그대로 초 단위 변환만 수행**

---

## 7. STOP_REASON 테이블

### 7.1 목적

* Stop 원인 코드 표준화

| 컬럼명               | 설명                             |
| ----------------- | ------------------------------ |
| stop_reason_code  | Stop 코드                        |
| stop_reason_name  | Stop 명칭                        |
| stop_reason_group | WAIT / ERROR / SETUP / QUALITY |

> 그룹은 **후처리 분류값**, 로그 파싱 대상 아님

---

## 8. STOP_LOG 테이블 (u01)

### 8.1 대상

* u01의 `Stop information per machine`

| 컬럼명              | 설명    | 파싱 규칙         |
| ---------------- | ----- | ------------- |
| stop_log_id      | PK    | 시스템 생성        |
| lot_machine_id   | FK    | LOT_MACHINE   |
| stop_reason_code | FK    | STOP_REASON   |
| duration_sec     | 정지 시간 | Stop Time → 초 |
| stop_count       | 발생 횟수 | Stop Count    |
| source_file_id   | 파일 FK | FILE.file_id  |

> 개별 Stop 이벤트로 분해하지 않음

---

## 9. PICKUP_ERROR_SUMMARY (u03)

### 9.1 대상

* u03 Pickup / Error Summary

| 컬럼명                                 | 설명 |
| ----------------------------------- | -- |
| lot_machine_id                      |    |
| total_pickup_count                  |    |
| total_error_count                   |    |
| pickup_error_count                  |    |
| recognition_error_count             |    |
| thick_error_count                   |    |
| placement_error_count               |    |
| part_drop_error_count               |    |
| transfer_unit_part_drop_error_count |    |
| pre_pickup_inspection_error_count   |    |

---

## 10. COMPONENT 테이블 (u03)

### 10.1 Component 식별 기준

```
component_id = hash(
  machine_id +
  table_id +
  feeder_id +
  feeder_serial +
  nozzle_changer +
  nozzle_holder +
  nozzle_serial
)
```

| 컬럼명            | 설명 |
| -------------- | -- |
| component_id   |    |
| machine_id     |    |
| table_id       |    |
| feeder_id      |    |
| feeder_serial  |    |
| nozzle_changer |    |
| nozzle_holder  |    |
| nozzle_serial  |    |
| part_number    |    |
| library_name   |    |

---

## 11. COMPONENT_PICKUP_SUMMARY (u03)

| 컬럼명                     | 설명 |
| ----------------------- | -- |
| lot_machine_id          |    |
| component_id            |    |
| pickup_count            |    |
| error_count             |    |
| pickup_error_count      |    |
| recognition_error_count |    |
| source_file_id          |    |

---

## 12. 파일 간 Join 규칙

* u01 ↔ u03 공통 키

```
lot_name + line_id + stage_no + machine_order
```

* 분석 Join 기준: `lot_machine_id`

---

## 13. 명시적 제한 사항

* 개별 Cycle 이벤트 ❌
* Stop Start/End 타임라인 ❌
* PPM / Error Rate 저장 ❌ (분석 시 계산)

---

## 14. 문서 역할 요약

* ERD: **구조 정의**
* 본 문서: **파싱 구현 규칙**
* HTML: **검증/레퍼런스 결과물**
