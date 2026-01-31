# 📘 Log Data Column Dictionary

본 문서는 **SMT 설비 로그(u01 / u03) 및 파일명 규칙을 기반으로 생성 가능한 데이터 컬럼 정의서**이다.  
HTML 리포트는 본 컬럼들의 **집계 결과물**이며, 본 문서에 정의된 컬럼 범위를 초과하지 않는다.

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
| boa
