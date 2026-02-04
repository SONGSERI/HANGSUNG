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
# Table Loader
# =========================
def load_table(table_name: str) -> pd.DataFrame:
    engine = get_engine()
    return pd.read_sql(f'SELECT * FROM "{table_name}"', engine)
