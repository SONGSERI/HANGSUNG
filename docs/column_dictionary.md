# Column Dictionary

본 문서는 SMT 설비 Raw 운전 데이터를 해석하여 구성한
분석용 데이터셋의 컬럼 정의를 설명한다.

---

## LOT

| Column | Type | Description |
|------|------|-------------|
| lot_id | bigint | 내부 Lot 식별자 |
| product_id | varchar | 제품 ID |
| product_rev | int | 제품 Revision |
| plan_id | varchar | 생산 계획 ID |
| lot_name | varchar | Lot 명 |
| lot_no | int | Lot 번호 |
| stage_no | int | 생산 Stage |
| lane_no | int | 생산 Lane |
| output_qty | int | 출력/계획 수량 |
| lot_board_qty | int | Lot 기준 Board 수 |
| lot_module_qty | int | Lot 기준 Module 수 |

---

## MACHINE_RUN

| Column | Type | Description |
|------|------|-------------|
| run_id | bigint | 설비 실행 단위 ID |
| lot_id | bigint | Lot ID (FK) |
| machine_id | varchar | 설비 ID |
| stage_no | int | 생산 Stage |
| lane_no | int | 생산 Lane |
| collect_time | timestamp | Raw 데이터 수집 시각 |

---

## MACHINE_TIME_SUMMARY

| Column | Type | Description |
|------|------|-------------|
| run_id | bigint | 실행 ID (PK, FK) |
| power_on_sec | float | 전원 ON 시간 |
| prod_time_sec | float | 생산 시간 |
| actual_run_sec | float | 실제 가동 시간 |
| idle_sec | float | 유휴 시간 |
| mount_sec | float | 실장 시간 |
| load_sec | float | 보드 로딩 시간 |
| brcg_sec | float | 보드 인식 시간 |
| total_stop_sec | float | 총 정지 시간 |
| front_wait_sec | float | 전공정 대기 시간 |
| rear_wait_sec | float | 후공정 대기 시간 |
| program_wait_sec | float | 프로그램 대기 시간 |
| mc_front_wait_sec | float | 설비 전방 대기 시간 |

---

## MACHINE_STOP_SUMMARY

| Column | Type | Description |
|------|------|-------------|
| run_id | bigint | 실행 ID (PK, FK) |
| safety_stop_sec | float | 안전 정지 시간 |
| safety_stop_cnt | int | 안전 정지 횟수 |
| pickup_err_stop_sec | float | 픽업 에러 정지 시간 |
| pickup_err_cnt | int | 픽업 에러 횟수 |
| recog_err_stop_sec | float | 인식 에러 정지 시간 |
| recog_err_cnt | int | 인식 에러 횟수 |
| prod_related_stop_sec | float | 생산 관련 정지 시간 |
| other_stop_sec | float | 기타 정지 시간 |

---

## PRODUCTION_QUALITY_SUMMARY

| Column | Type | Description |
|------|------|-------------|
| run_id | bigint | 실행 ID (PK, FK) |
| board_cnt | int | 처리 보드 수 |
| module_cnt | int | 처리 모듈 수 |
| total_pickup_cnt | bigint | 총 픽업 횟수 |
| total_mount_cnt | bigint | 정상 실장 수 |
| pickup_miss_cnt | int | 픽업 미스 수 |
| recog_miss_cnt | int | 인식 미스 수 |

---
