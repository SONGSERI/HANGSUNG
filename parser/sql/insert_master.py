from stop_reason_master import STOP_REASON_MASTER
from db import get_conn

SQL_INSERT_STOP_REASON = """
INSERT INTO stop_reason (
    stop_reason_code,
    stop_reason_name,
    stop_reason_group
)
VALUES (%s, %s, %s)
ON CONFLICT (stop_reason_code) DO NOTHING
"""

def insert_stop_reason_master():
    rows = [
        (v["code"], k, v["group"])
        for k, v in STOP_REASON_MASTER.items()
    ]

    conn = get_conn()
    with conn.cursor() as cur:
        cur.executemany(SQL_INSERT_STOP_REASON, rows)
    conn.commit()
    conn.close()
