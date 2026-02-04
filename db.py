import pandas as pd
from sqlalchemy import create_engine


def get_engine(
    user="song",
    password="a12345!@#",
    host="host.docker.internal",
    port=5432,
    dbname="song",
):
    url = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
    return create_engine(url)


def load_table(engine, table_name: str) -> pd.DataFrame:
    return pd.read_sql(f"SELECT * FROM {table_name}", engine)
