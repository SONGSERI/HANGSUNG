import os
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

# =========================
# DB Config (Single Source)
# =========================
DB_CONFIG = {
    "user": os.getenv("DB_USER", "song"),
    "password": os.getenv("DB_PASSWORD", "a12345"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", 5432)),
    "dbname": os.getenv("DB_NAME", "song"),
}


# =========================
# Engine
# =========================
def get_engine():
    cfg = DB_CONFIG
    url = (
        f"postgresql+psycopg2://{cfg['user']}:{cfg['password']}"
        f"@{cfg['host']}:{cfg['port']}/{cfg['dbname']}"
    )
    return create_engine(url, pool_pre_ping=True)


# =========================
# Health Check
# =========================
def db_health_check():
    cfg = DB_CONFIG
    result = {}

    # 1) psycopg2 direct
    try:
        conn = psycopg2.connect(
            user=cfg["user"],
            password=cfg["password"],
            host=cfg["host"],
            port=cfg["port"],
            dbname=cfg["dbname"],
            connect_timeout=5,
        )
        conn.close()
        result["direct_ok"] = True
        result["direct_msg"] = "✅ PostgreSQL direct connection OK"
    except Exception as e:
        result["direct_ok"] = False
        result["direct_msg"] = f"❌ PostgreSQL direct connection FAILED: {e}"

    # 2) SQLAlchemy
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        result["sqlalchemy_ok"] = True
        result["sqlalchemy_msg"] = "✅ SQLAlchemy connection OK"
    except SQLAlchemyError as e:
        result["sqlalchemy_ok"] = False
        result["sqlalchemy_msg"] = f"❌ SQLAlchemy connection FAILED: {e}"

    return result


# =========================
# Table Loader
# =========================
def load_table(table_name: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(f'SELECT * FROM "{table_name}"', engine)
