#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

PG_PASS="$(bashio::config 'postgres_password')"
PG_HOST="db21ed7f-postgres-latest"
PG_USER="postgres"
export PGPASSWORD="${PG_PASS}"

run_sql_file() {
  local db="$1"
  local file="$2"
  if psql -h "${PG_HOST}" -U "${PG_USER}" -d "${db}" -v ON_ERROR_STOP=1 -f "${file}" >/dev/null 2>&1; then
    bashio::log.info "Applied ${file} on ${db}"
    return 0
  fi
  bashio::log.warning "Skipped ${file} on ${db} (table missing or already applied)"
  return 1
}

run_cleanup() {
  local db="$1"
  local removed=0
  local challenges=0

  if psql -h "${PG_HOST}" -U "${PG_USER}" -d "${db}" -tAc \
    "select to_regprocedure('public.process_old_remove_word_reports()') is not null;" \
    | grep -q t; then
    removed="$(psql -h "${PG_HOST}" -U "${PG_USER}" -d "${db}" -tAc \
      "select public.process_old_remove_word_reports();" | tr -d '[:space:]')"
    bashio::log.info "${db}: processed ${removed:-0} old remove word_reports"
  fi

  if psql -h "${PG_HOST}" -U "${PG_USER}" -d "${db}" -tAc \
    "select to_regprocedure('public.cleanup_old_challenges()') is not null;" \
    | grep -q t; then
    challenges="$(psql -h "${PG_HOST}" -U "${PG_USER}" -d "${db}" -tAc \
      "select public.cleanup_old_challenges();" | tr -d '[:space:]')"
    bashio::log.info "${db}: cleaned ${challenges:-0} old challenge cards"
  fi
}

install_functions() {
  for db in petko_sr petko_en; do
    run_sql_file "${db}" /sql/word-remove-function.sql || true
  done
  run_sql_file petko_sr /sql/challenge-cleanup-function.sql || true
  run_sql_file petko_en /sql/challenge-cleanup-function.sql || true
}

seconds_until_next_run() {
  local minute second wait
  minute=$((10#$(date +%M)))
  second=$((10#$(date +%S)))
  wait=$(( (5 - minute) * 60 - second ))
  if (( wait <= 0 )); then
    wait=$(( wait + 3600 ))
  fi
  echo "${wait}"
}

bashio::log.info "Installing Petko maintenance SQL functions..."
install_functions
run_cleanup petko_sr
run_cleanup petko_en

bashio::log.info "Scheduler active: word remove + challenge cleanup every hour at :05 (Belgrade day boundary for words)"

while true; do
  sleep "$(seconds_until_next_run)"
  run_cleanup petko_sr
  run_cleanup petko_en
done
