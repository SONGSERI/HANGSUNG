# 📘 Log Data Column Dictionary

본 문서는 **SMT 설비 로그(u01 / u03) 및 파일명 규칙을 기반으로 생성 가능한 데이터 컬럼 정의서**이다.  
HTML 리포트는 본 컬럼들의 **집계 결과물**

---

## 1. FILE — 로그 파일 메타데이터

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| file_id | string (PK) | 파일 내부 식별자 | 시스템 생성 |
| file_name | string | 원본 로그 파일명 | 파일명 |
| file_datetime | datetime | 파일 생성 일시 (YYYYMMDD 기준) | 파일명 |
| file_sequence | int | 일자 내 파일 시퀀스 번호 | 파일명 |
| line_id | string | 라인 번호 (예: 05) | 파일명 |
| process_no | int | 공정 번호 | 파일명 |
| stage_no | int | Stage 번호 | 파일명 |
| machine_order | int | Machine 순번 (1~N) | 파일명 |
| lot_name | string | Lot 이름 | 파일명 |
| file_type | string | 로그 타입 (u01 / u03) | 확장자 |

---

## 2. LOT — Lot 정보

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| lot_id | string (PK) | Lot 내부 식별자 | 시스템 생성 |
| lot_name | string | Lot 명 | 파일명 / HTML |
| start_time | datetime | Lot 시작 시각 | 로그 |
| end_time | datetime | Lot 종료 시각 | 로그 |
| lane | string | 생산 Lane | HTML |

---

## 3. MACHINE — 설비 마스터

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| machine_id | string (PK) | 설비 식별자 | 시스템 생성 |
| line_id | string | 라인 번호 | 파일명 |
| stage_no | int | Stage 번호 | 파일명 |
| machine_order | int | Machine 순번 | 파일명 |

---

## 4. LOT_MACHINE — Lot × Machine 실행 단위

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| lot_machine_id | string (PK) | Lot-Machine 실행 식별자 | 시스템 생성 |
| lot_id | string (FK) | Lot 식별자 | LOT |
| machine_id | string (FK) | Machine 식별자 | MACHINE |

---

## 5. MACHINE_TIME_SUMMARY — 설비 시간 집계

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| lot_machine_id | string (FK) | Lot-Machine 식별자 | LOT_MACHINE |
| power_on_time_sec | int | Power ON 누적 시간(초) | u01 |
| running_time_sec | int | Running 시간 | u01 |
| real_running_time_sec | int | 실제 생산 시간 | u01 |
| total_stop_time_sec | int | 총 정지 시간 | u01 |
| transfer_time_sec | int | 이송 시간 | u01 |
| board_recognition_time_sec | int | 보드 인식 시간 | u01 |
| placement_time_sec | int | 실장 시간 | u01 |

---

## 6. STOP_REASON — 정지 사유 코드 사전

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| stop_reason_code | string (PK) | 정지 사유 코드 | HTML |
| stop_reason_name | string | 정지 사유 명 | HTML |
| stop_reason_group | string | WAIT / ERROR / QUALITY / SETUP | 분류 |

---

## 7. STOP_LOG — 정지 이력 (누적 기반)

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| stop_log_id | string (PK) | 정지 이력 식별자 | 시스템 생성 |
| lot_machine_id | string (FK) | Lot-Machine 식별자 | LOT_MACHINE |
| stop_reason_code | string (FK) | 정지 사유 코드 | u01 |
| duration_sec | int | 정지 누적 시간(초) | u01 |
| stop_count | int | 정지 발생 횟수 | u01 |
| source_file_id | string (FK) | 출처 파일 ID | FILE |

---

## 8. PICKUP_ERROR_SUMMARY — 설비 품질 요약

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| lot_machine_id | string (FK) | Lot-Machine 식별자 | LOT_MACHINE |
| total_pickup_count | int | 총 Pickup 횟수 | u03 |
| total_error_count | int | 총 에러 수 | u03 |
| pickup_error_count | int | Pickup 에러 수 | u03 |
| recognition_error_count | int | 인식 에러 수 | u03 |
| thick_error_count | int | 두께 에러 수 | u03 |
| placement_error_count | int | 실장 에러 수 | u03 |
| part_drop_error_count | int | 부품 낙하 에러 | u03 |
| transfer_unit_part_drop_error_count | int | 이송부 낙하 에러 | u03 |
| pre_pickup_inspection_error_count | int | 픽업 전 검사 에러 | u03 |

---

## 9. COMPONENT — 구성요소 마스터

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| component_id | string (PK) | Component 식별자 | 시스템 생성 |
| machine_id | string (FK) | 설비 식별자 | MACHINE |
| table_id | string | Table 번호 | u03 |
| feeder_id | string | Feeder 번호 | u03 |
| feeder_serial | string | Feeder 시리얼 | u03 |
| nozzle_changer | string | Nozzle Changer 번호 | u03 |
| nozzle_holder | string | Nozzle Holder 번호 | u03 |
| nozzle_serial | string | Nozzle 시리얼 | u03 |
| part_number | string | 부품 번호 | u03 |
| library_name | string | 라이브러리 명 | u03 |

---

## 10. COMPONENT_PICKUP_SUMMARY — 구성요소별 집계

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| lot_machine_id | string (FK) | Lot-Machine 식별자 | LOT_MACHINE |
| component_id | string (FK) | Component 식별자 | COMPONENT |
| pickup_count | int | Pickup 횟수 | u03 |
| error_count | int | 에러 수 | u03 |
| pickup_error_count | int | Pickup 에러 수 | u03 |
| recognition_error_count | int | 인식 에러 수 | u03 |
| source_file_id | string (FK) | 출처 파일 ID | FILE |

---

## 11. TAG_CATEGORY — 태그 분류

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| tag_category_id | string (PK) | 태그 분류 식별자 | 시스템 생성 |
| tag_category_name | string | 태그 분류명 | 로그 Section / 운영정의 |
| parent_category_id | string (FK) | 상위 태그 분류 ID | 운영정의 |
| description | string | 분류 설명 | 운영정의 |

---

## 12. TAG_INFO — 태그 기준 정보

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| tag_id | string (PK) | 태그 식별자 | 시스템 생성 |
| tag_name | string | 태그명 (`Section.Key`) | u01/u03 raw |
| tag_category_id | string (FK) | 태그 분류 식별자 | TAG_CATEGORY |
| machine_id | string (FK) | 설비 식별자(옵션) | MACHINE |
| data_type | string | 데이터 타입 (`float`/`string`) | raw 값 판별 |
| unit | string | 단위 | 운영정의 |
| source_system | string | 수집 시스템 (`u01`/`u03`) | 파일 확장자 |
| is_active | bool | 사용 여부 | 기본값(true) |
| description | string | 태그 설명 | 파싱 생성 |

---

## 13. TAG_SPEC — 태그 기준값/스펙

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| tag_spec_id | string (PK) | 스펙 식별자 | 시스템 생성 |
| tag_id | string (FK) | 태그 식별자 | TAG_INFO |
| spec_type | string | 기준 타입 (`TARGET/LCL/UCL`) | 운영정의 |
| spec_value | float | 기준 값 | 운영정의 |
| effective_from | datetime | 적용 시작 시각 | 운영정의 |
| effective_to | datetime | 적용 종료 시각 | 운영정의 |

---

## 14. TAG_REALTIME — 태그 실시간 값

| 컬럼명 | 타입 | 설명 | 출처 |
|---|---|---|---|
| tag_data_id | string (PK) | 태그 데이터 식별자 | 시스템 생성 |
| tag_id | string (FK) | 태그 식별자 | TAG_INFO |
| machine_id | string (FK) | 설비 식별자(옵션) | MACHINE |
| recorded_at | datetime | 측정 시각 | 로그 `Date=` / 파일일자 fallback |
| tag_value | float | 태그 측정값 | u01/u03 raw 숫자값 |
| quality_flag | string | 품질 플래그 | 운영정의 |
| source_file_id | string (FK) | 출처 파일 ID | FILE |

---

## 15. ⚠️ 데이터 범위 명시 (중요)

**본 로그로 생성 불가능한 데이터**
- 개별 Pick 이벤트 단건 타임라인
- Stop 시작/종료 시각 (누적 데이터만 존재)
- PPM, Error Rate (모두 파생 계산)

---
