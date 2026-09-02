#!/usr/bin/env python3
"""Create glab_trading DB and apply schema on HA Postgres."""
from __future__ import annotations

import sys
from pathlib import Path

import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

PG_HOST = "192.168.1.6"
PG_USER = "postgres"
PG_PASS = "homeassistant"
DB_NAME = "glab_trading"
SQL_FILE = Path(r"D:\projekti\g-lab-trading-web\sql\001_schema.sql")


def main() -> int:
    print(f"Connecting to Postgres @ {PG_HOST}...")
    admin = psycopg2.connect(host=PG_HOST, port=5432, dbname="postgres", user=PG_USER, password=PG_PASS)
    admin.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = admin.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if not cur.fetchone():
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"Created database {DB_NAME}")
    else:
        print(f"Database {DB_NAME} already exists")
    cur.close()
    admin.close()

    sql = SQL_FILE.read_text(encoding="utf-8")
    conn = psycopg2.connect(host=PG_HOST, port=5432, dbname=DB_NAME, user=PG_USER, password=PG_PASS)
    cur = conn.cursor()
    cur.execute(sql)
    conn.commit()
    cur.execute("NOTIFY pgrst, 'reload schema'")
    conn.commit()
    cur.close()
    conn.close()
    print("Schema applied OK")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
