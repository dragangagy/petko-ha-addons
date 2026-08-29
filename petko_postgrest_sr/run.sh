#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

DB_NAME="$(bashio::config 'db_name')"
PG_PASS="$(bashio::config 'postgres_password')"
JWT_SECRET="$(bashio::config 'jwt_secret')"
PG_HOST="db21ed7f-postgres-latest"

export PGRST_DB_URI="postgresql://postgres:${PG_PASS}@${PG_HOST}:5432/${DB_NAME}?sslmode=disable"
export PGRST_DB_SCHEMAS="public"
export PGRST_DB_ANON_ROLE="anon"
export PGRST_JWT_SECRET="${JWT_SECRET}"
export PGRST_SERVER_PORT="13001"
export PGRST_SERVER_HOST="127.0.0.1"
export PGRST_SERVER_CORS_ALLOWED_ORIGINS="*"
export PGRST_DB_MAX_ROWS="10000"

bashio::log.info "Starting PostgREST SR -> ${PG_HOST}/${DB_NAME}:13001 (nginx CORS proxy on :3001)"
/usr/local/bin/postgrest &
exec nginx -c /etc/nginx/nginx.conf -g 'daemon off;'
