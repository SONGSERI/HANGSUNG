


import psycopg2
from psycopg2.extras import execute_batch

def get_conn():
    return psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="mes",
        user="mes_user",
        password="mes_password",
    )

def execute_upsert(conn, sql, rows):
    if not rows:
        return
    with conn.cursor() as cur:
        execute_batch(cur, sql, rows)
    conn.commit()
