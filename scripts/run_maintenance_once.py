#!/usr/bin/env python3
"""Run Petko DB maintenance once (word remove + challenge cleanup)."""
from __future__ import annotations

import psycopg2

PG = dict(host="192.168.1.6", port=5432, user="postgres", password="homeassistant")

for db in ("petko_sr", "petko_en"):
    with psycopg2.connect(dbname=db, **PG) as conn, conn.cursor() as cur:
        cur.execute("SELECT public.process_old_remove_word_reports()")
        removed = cur.fetchone()[0]
        print(f"{db}: removed reports processed = {removed}")
        try:
            cur.execute("SELECT public.cleanup_old_challenges()")
            cleaned = cur.fetchone()[0]
            print(f"{db}: challenges cleaned = {cleaned}")
        except Exception as exc:
            print(f"{db}: challenge cleanup skipped ({exc})")
        conn.commit()
