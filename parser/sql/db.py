# DB: PostgreSQL
# 드라이버: psycopg2
# 방식: UPSERT(중복 허용, 재실행 안전)


import os

import psycopg2
from psycopg2.extras import execute_batch

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "5432")),
        dbname=os.getenv("DB_NAME", "song"),
        user=os.getenv("DB_USER", "song"),
        password=os.getenv("DB_PASSWORD", ""),
    )

def execute_upsert(conn, sql, rows):
    if not rows:
        return
    with conn.cursor() as cur:
        execute_batch(cur, sql, rows)
    conn.commit()
