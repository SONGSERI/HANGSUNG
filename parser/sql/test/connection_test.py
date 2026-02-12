import psycopg2
from psycopg2 import sql

DB_CONFIG = {
    "host": "192.168.200.105",
    "port": 5432,
    "database": "nexedge",
    "user": "analysis",
    "password": "analysis1!",
}

def main():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()

        # 서버 버전 확인
        cur.execute("SELECT version();")
        version = cur.fetchone()
        print("Connected successfully.")
        print("PostgreSQL version:")
        print(version[0])

        # 현재 DB 확인
        cur.execute("SELECT current_database();")
        dbname = cur.fetchone()
        print("Current database:", dbname[0])

        cur.close()
        conn.close()

    except Exception as e:
        print("Connection failed.")
        print("Error:", e)

if __name__ == "__main__":
    main()
