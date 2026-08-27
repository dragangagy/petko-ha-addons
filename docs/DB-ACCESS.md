# Petko PostgreSQL — brzi pristup

## Web (Adminer) — preporuka

1. HA → Add-ons → **Petko DB Admin** → Start
2. Otvori: **http://192.168.1.6:8080**
   - ili dupli klik: `scripts/open-petko-db-admin.bat`
3. Login:
   - **System:** PostgreSQL
   - **Server:** `db21ed7f-postgres-latest`
   - **Username:** `postgres`
   - **Password:** `homeassistant` (iz Postgres 17 add-on config)
   - **Database:** `petko_sr` ili `petko_en`

## DBeaver / pgAdmin sa PC-a (LAN)

| Polje | Vrednost |
|-------|----------|
| Host | `192.168.1.6` |
| Port | `5432` |
| User | `postgres` |
| Password | `homeassistant` |
| Database | `petko_sr` ili `petko_en` |

Moraš biti na kućnoj WiFi mreži.

## Korisni upiti

```sql
-- Prijave reči
SELECT word, action, nickname, created_at
FROM word_reports ORDER BY created_at DESC LIMIT 50;

-- Deaktivirane reči
SELECT word, note, updated_at FROM words WHERE active = false ORDER BY updated_at DESC LIMIT 30;

-- Dodaj reč
INSERT INTO words (word, meaning, active)
VALUES ('тест1', 'Test reč.', true)
ON CONFLICT (word) DO UPDATE SET active = true, meaning = EXCLUDED.meaning;

-- Izazovi u toku
SELECT code, status, creator, opponent FROM challenges ORDER BY created_at DESC LIMIT 20;

-- Nastavci igara
SELECT nickname, mode, challenge_code, updated_at FROM game_sessions WHERE status = 'in_progress';
```

## Automatsko uklanjanje prijavljenih reči

Add-on **Petko DB Maintenance** svakog sata u **:05**:
- `remove` prijave starije od današnjeg dana (po Beogradu) → reč `active=false`, prijava se briše
- `add` prijave ostaju za ručnu proveru

Challenge cleanup takođe radi na obe baze (stare kartice izazova).
