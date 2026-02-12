# MSSQL BeingPlus 프로시저 연동 가이드 (Python)

## 1) 목적
`dbo.INSERT_BEINGPLUS_DATA` 프로시저를 애플리케이션의 표준 저장 인터페이스로 호출하기 위한 템플릿

---

## 2) Python 호출 방식
- 템플릿 코드: `parser/sql/mssql_beingplus.py`
- 드라이버: `pyodbc`
- 핵심 포인트:
  - OUTPUT 파라미터(`@RS_CODE`, `@RS_MSG`)는 T-SQL 래퍼에서 `SELECT`로 반환
  - 앱은 `RS_CODE`로 성공/실패 판정 (`S`/`E`)
  - 실패 시 재시도 + rollback

```python
from datetime import datetime
from mssql_beingplus import (
    get_mssql_conn,
    BeingPlusTagEvent,
    save_event_with_retry,
)

conn = get_mssql_conn()
try:
    event = BeingPlusTagEvent(
        line_code="10",
        work_code="WC-001",
        equip_code="EQ-001",
        address="D00235",
        tag_type="0",
        value="22.45",
        insert_dt=datetime.now(),
    )
    result = save_event_with_retry(conn, event, retries=2)
    print(result.rs_code, result.rs_msg)
finally:
    conn.close()
```

---

## 3) 애플리케이션 DB 구조 제안
프로시저 직접 호출만으로도 저장은 가능하지만, 운영 안정성을 위해 아래 2개 테이블을 앱 DB(또는 동일 MSSQL)에 추가하는 것을 권장합니다.

### 3-1) 입력 큐 테이블 (`beingplus_ingest_queue`)
- 목적: 수집 직후 원본 적재(내결함성)
- 사용: 네트워크/DB 장애 시 재처리 기반

```sql
CREATE TABLE dbo.beingplus_ingest_queue (
    queue_id            BIGINT IDENTITY(1,1) PRIMARY KEY,
    line_code           NVARCHAR(20) NOT NULL,
    work_code           NVARCHAR(20) NOT NULL,
    equip_code          NVARCHAR(20) NOT NULL,
    address             NVARCHAR(20) NOT NULL,
    tag_type            NVARCHAR(10) NOT NULL,
    tag_value           NVARCHAR(50) NOT NULL,
    device_dt           DATETIME2(3) NOT NULL,
    receive_dt          DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    status              NVARCHAR(20) NOT NULL DEFAULT 'PENDING', -- PENDING/SENT/FAILED
    retry_count         INT NOT NULL DEFAULT 0,
    last_error          NVARCHAR(1000) NULL
);

CREATE INDEX IX_beingplus_queue_status_receive
    ON dbo.beingplus_ingest_queue(status, receive_dt);
```

### 3-2) 전송 로그 테이블 (`beingplus_proc_log`)
- 목적: 프로시저 응답 추적/장애 분석
- 사용: `RS_CODE`, `RS_MSG`, 지연시간(ms) 기록

```sql
CREATE TABLE dbo.beingplus_proc_log (
    proc_log_id         BIGINT IDENTITY(1,1) PRIMARY KEY,
    queue_id            BIGINT NULL,
    line_code           NVARCHAR(20) NOT NULL,
    work_code           NVARCHAR(20) NOT NULL,
    equip_code          NVARCHAR(20) NOT NULL,
    address             NVARCHAR(20) NOT NULL,
    tag_type            NVARCHAR(10) NOT NULL,
    tag_value           NVARCHAR(50) NOT NULL,
    device_dt           DATETIME2(3) NOT NULL,
    call_dt             DATETIME2(3) NOT NULL DEFAULT SYSUTCDATETIME(),
    elapsed_ms          INT NULL,
    rs_code             NVARCHAR(1) NULL,
    rs_msg              NVARCHAR(255) NULL
);

CREATE INDEX IX_beingplus_proc_log_call_dt
    ON dbo.beingplus_proc_log(call_dt);
```

---

## 4) 권장 처리 흐름
1. 태그 수신
2. `beingplus_ingest_queue` 적재 (`PENDING`)
3. 워커가 큐를 읽어 `INSERT_BEINGPLUS_DATA` 실행
4. 성공 시 `SENT`, 실패 시 `FAILED` + `retry_count++`
5. 모든 호출 결과를 `beingplus_proc_log`에 기록

---

## 5) 타입 매핑 가이드
- `tag_type`:
  - `0`: 누적 Product Qty
  - `1`: 순시 Product Qty
  - `2`: Status
  - `3`: Value
  - `4`: Alarm
- `tag_value`: 프로시저 정의가 `NVARCHAR(50)` 이므로 문자열로 전달
- `insert_dt`: `yyyy-MM-dd HH:mm:ss.fff` 형식 권장

---

## 6) 운영 체크리스트
- DB 연결 타임아웃 설정
- 재시도 횟수/간격(지수 백오프) 설정
- 큐 적체량 모니터링
- `RS_CODE='E'` 비율 알람
- 장비코드/주소 매핑 사전 관리
