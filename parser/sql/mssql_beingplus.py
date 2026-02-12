"""MSSQL BeingPlus 저장 프로시저 호출 템플릿.

프로시저:
    dbo.INSERT_BEINGPLUS_DATA

드라이버:
    pyodbc

설치:
    pip install pyodbc
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Tuple

import pyodbc


@dataclass(frozen=True)
class BeingPlusTagEvent:
    """장비 태그 이벤트 DTO."""

    line_code: str
    work_code: str
    equip_code: str
    address: str
    tag_type: str
    value: str
    insert_dt: datetime


@dataclass(frozen=True)
class ProcResult:
    """프로시저 실행 결과."""

    rs_code: str
    rs_msg: str

    @property
    def ok(self) -> bool:
        return self.rs_code == "S"


def get_mssql_conn() -> pyodbc.Connection:
    """환경 변수 기반 MSSQL 연결 생성.

    환경 변수:
      - MSSQL_HOST (default: localhost)
      - MSSQL_PORT (default: 1433)
      - MSSQL_DB   (default: TEST)
      - MSSQL_USER (default: sa)
      - MSSQL_PASSWORD
      - MSSQL_DRIVER (default: ODBC Driver 18 for SQL Server)
      - MSSQL_TRUST_CERT (default: yes)
    """

    host = os.getenv("MSSQL_HOST", "localhost")
    port = os.getenv("MSSQL_PORT", "1433")
    db = os.getenv("MSSQL_DB", "TEST")
    user = os.getenv("MSSQL_USER", "sa")
    password = os.getenv("MSSQL_PASSWORD", "")
    driver = os.getenv("MSSQL_DRIVER", "ODBC Driver 18 for SQL Server")
    trust_cert = os.getenv("MSSQL_TRUST_CERT", "yes")

    conn_str = (
        f"DRIVER={{{driver}}};"
        f"SERVER={host},{port};"
        f"DATABASE={db};"
        f"UID={user};PWD={password};"
        "Encrypt=yes;"
        f"TrustServerCertificate={trust_cert};"
    )
    return pyodbc.connect(conn_str, autocommit=False)


def _fmt_insert_dt(dt: datetime) -> str:
    """MSSQL NVARCHAR(50) 포맷(yyyy-MM-dd HH:mm:ss.fff)."""

    return dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]


def call_insert_beingplus_data(
    conn: pyodbc.Connection,
    event: BeingPlusTagEvent,
) -> ProcResult:
    """INSERT_BEINGPLUS_DATA 실행.

    참고:
    - pyodbc는 OUTPUT 파라미터 바인딩이 직접적이지 않아
      T-SQL 래퍼를 통해 OUTPUT 값을 SELECT로 반환받는다.
    """

    ts = _fmt_insert_dt(event.insert_dt)

    sql = """
    DECLARE @RS_CODE NVARCHAR(1), @RS_MSG NVARCHAR(255);

    EXEC [dbo].[INSERT_BEINGPLUS_DATA]
         @LineCode = ?,
         @WorkCode = ?,
         @EquipCode = ?,
         @Address = ?,
         @Type = ?,
         @Value = ?,
         @InsertDT = ?,
         @RS_CODE = @RS_CODE OUTPUT,
         @RS_MSG = @RS_MSG OUTPUT;

    SELECT COALESCE(@RS_CODE, 'S') AS RS_CODE,
           COALESCE(@RS_MSG,  'EXECUTION COMPLETE!') AS RS_MSG;
    """

    with conn.cursor() as cur:
        cur.execute(
            sql,
            event.line_code,
            event.work_code,
            event.equip_code,
            event.address,
            event.tag_type,
            event.value,
            ts,
        )
        row = cur.fetchone()

    conn.commit()

    if row is None:
        return ProcResult(rs_code="E", rs_msg="No result returned from procedure")

    return ProcResult(rs_code=str(row.RS_CODE), rs_msg=str(row.RS_MSG))


def save_event_with_retry(
    conn: pyodbc.Connection,
    event: BeingPlusTagEvent,
    retries: int = 2,
) -> ProcResult:
    """단순 재시도 포함 저장 템플릿."""

    last: Optional[ProcResult] = None
    for _ in range(retries + 1):
        try:
            result = call_insert_beingplus_data(conn, event)
            last = result
            if result.ok:
                return result
        except pyodbc.Error as exc:
            conn.rollback()
            last = ProcResult(rs_code="E", rs_msg=f"pyodbc error: {exc}")

    return last or ProcResult(rs_code="E", rs_msg="Unknown error")


def example_usage() -> Tuple[str, str]:
    """로컬 수동 테스트 예시."""

    event = BeingPlusTagEvent(
        line_code="10",
        work_code="WC-001",
        equip_code="EQ-001",
        address="D00235",
        tag_type="0",
        value="22.45",
        insert_dt=datetime.now(),
    )

    conn = get_mssql_conn()
    try:
        result = save_event_with_retry(conn, event, retries=2)
        return result.rs_code, result.rs_msg
    finally:
        conn.close()


if __name__ == "__main__":
    code, msg = example_usage()
    print(code, msg)
