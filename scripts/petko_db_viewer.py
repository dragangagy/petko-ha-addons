#!/usr/bin/env python3
"""Local Petko DB browser (LAN only). Run: python petko_db_viewer.py"""
from __future__ import annotations

import html
import webbrowser
from pathlib import Path

import psycopg2
from flask import Flask, redirect, render_template_string, request, url_for

PG = dict(host="192.168.1.6", port=5432, user="postgres", password="homeassistant")
DBS = ("petko_sr", "petko_en")

app = Flask(__name__)

PAGE = """
<!doctype html>
<html lang="sr"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Petko DB</title>
<style>
body{font-family:Segoe UI,sans-serif;margin:16px;background:#0f172a;color:#e2e8f0}
a{color:#7dd3fc;margin-right:12px}
.card{background:#1e293b;border:1px solid #334155;border-radius:10px;padding:14px;margin:12px 0;overflow:auto}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{border:1px solid #334155;padding:6px 8px;text-align:left;vertical-align:top}
th{background:#0b1220}
input,select,textarea,button{font:inherit;padding:8px;border-radius:8px;border:1px solid #475569;background:#0f172a;color:#e2e8f0}
button{cursor:pointer;background:#1d4ed8;border-color:#2563eb}
.msg{padding:10px;border-radius:8px;background:#14532d;margin:10px 0}
.err{background:#7f1d1d}
</style></head><body>
<h1>Petko DB — {{ db }}</h1>
<p>
  Baza:
  {% for name in dbs %}
    {% if name == db %}<strong>{{ name }}</strong>{% else %}<a href="{{ url_for('home', db=name) }}">{{ name }}</a>{% endif %}
  {% endfor %}
</p>
<p>
  <a href="{{ url_for('reports', db=db) }}">Prijave reči</a>
  <a href="{{ url_for('words', db=db) }}">Rečnik</a>
  <a href="{{ url_for('challenges', db=db) }}">Izazovi</a>
  <a href="{{ url_for('sessions', db=db) }}">Nastavci igara</a>
  <a href="{{ url_for('add_word', db=db) }}">+ Nova reč</a>
  <a href="{{ url_for('maintenance', db=db) }}">▶ Održavanje sada</a>
</p>
{% if message %}<div class="msg">{{ message }}</div>{% endif %}
{% if error %}<div class="msg err">{{ error }}</div>{% endif %}
<div class="card">{{ body|safe }}</div>
</body></html>
"""


def connect(db: str):
    return psycopg2.connect(dbname=db, **PG)


def table_html(cur, rows, columns) -> str:
    if not rows:
        return "<p>Nema redova.</p>"
    head = "".join(f"<th>{html.escape(str(c))}</th>" for c in columns)
    body = []
    for row in rows:
        cells = "".join(f"<td>{html.escape('' if v is None else str(v))}</td>" for v in row)
        body.append(f"<tr>{cells}</tr>")
    return f"<table><thead><tr>{head}</tr></thead><tbody>{''.join(body)}</tbody></table>"


def render_page(db: str, body: str, message: str = "", error: str = ""):
    return render_template_string(PAGE, db=db, dbs=DBS, body=body, message=message, error=error)


@app.route("/")
def home():
    db = request.args.get("db", DBS[0])
    body = "<p>Izaberi sekciju iz menija. Radi samo na kućnoj mreži (192.168.1.6:5432).</p>"
    return render_page(db, body)


@app.route("/reports")
def reports():
    db = request.args.get("db", DBS[0])
    with connect(db) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT word, action, nickname, created_at FROM word_reports "
            "ORDER BY created_at DESC LIMIT 100"
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return render_page(db, table_html(rows, cols))


@app.route("/words")
def words():
    db = request.args.get("db", DBS[0])
    q = request.args.get("q", "").strip()
    with connect(db) as conn, conn.cursor() as cur:
        if q:
            cur.execute(
                "SELECT word, active, left(meaning, 80), updated_at FROM words "
                "WHERE word ILIKE %s ORDER BY word LIMIT 100",
                (f"%{q}%",),
            )
        else:
            cur.execute(
                "SELECT word, active, left(meaning, 80), updated_at FROM words "
                "WHERE active = true ORDER BY updated_at DESC LIMIT 100"
            )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    form = (
        f'<form method="get"><input name="q" value="{html.escape(q)}" placeholder="Pretraži reč"> '
        f'<input type="hidden" name="db" value="{html.escape(db)}"><button>Traži</button></form>'
    )
    return render_page(db, form + table_html(rows, cols))


@app.route("/challenges")
def challenges():
    db = request.args.get("db", DBS[0])
    with connect(db) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT code, status, creator, opponent, creator_solved, opponent_solved, created_at "
            "FROM challenges ORDER BY created_at DESC LIMIT 50"
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return render_page(db, table_html(rows, cols))


@app.route("/sessions")
def sessions():
    db = request.args.get("db", DBS[0])
    with connect(db) as conn, conn.cursor() as cur:
        cur.execute(
            "SELECT nickname, mode, challenge_code, status, updated_at "
            "FROM game_sessions WHERE status = 'in_progress' ORDER BY updated_at DESC LIMIT 50"
        )
        rows = cur.fetchall()
        cols = [d[0] for d in cur.description]
    return render_page(db, table_html(rows, cols))


@app.route("/add-word", methods=["GET", "POST"])
def add_word():
    db = request.args.get("db", DBS[0])
    if request.method == "POST":
        word = request.form.get("word", "").strip()
        meaning = request.form.get("meaning", "").strip()
        if not word:
            return render_page(db, "", error="Unesi reč.")
        with connect(db) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO words (word, meaning, active) VALUES (%s, %s, true) "
                "ON CONFLICT (word) DO UPDATE SET meaning = EXCLUDED.meaning, active = true, updated_at = now()",
                (word, meaning or None),
            )
            conn.commit()
        return redirect(url_for("words", db=db))
    form = """
    <form method="post">
      <p><label>Reč<br><input name="word" maxlength="5" required></label></p>
      <p><label>Značenje<br><textarea name="meaning" rows="3" style="width:100%"></textarea></label></p>
      <button>Sačuvaj</button>
    </form>
    """
    return render_page(db, form)


@app.route("/maintenance")
def maintenance():
    db = request.args.get("db", DBS[0])
    messages = []
    for name in DBS:
        with connect(name) as conn, conn.cursor() as cur:
            cur.execute("SELECT public.process_old_remove_word_reports()")
            removed = cur.fetchone()[0]
            messages.append(f"{name}: uklonjeno {removed} starih remove prijava")
            try:
                cur.execute("SELECT public.cleanup_old_challenges()")
                cleaned = cur.fetchone()[0]
                messages.append(f"{name}: očišćeno {cleaned} starih izazova")
            except Exception:
                pass
            conn.commit()
    return render_page(db, "<p>Gotovo.</p>", message=" · ".join(messages))


def main() -> None:
    url = "http://127.0.0.1:8765/"
    print(f"Petko DB viewer: {url}")
    print("Ctrl+C za stop.")
    webbrowser.open(url)
    app.run(host="127.0.0.1", port=8765, debug=False)


if __name__ == "__main__":
    main()
