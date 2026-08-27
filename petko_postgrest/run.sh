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
export PGRST_SERVER_PORT="3000"
export PGRST_SERVER_HOST="0.0.0.0"

bashio::log.info "Starting PostgREST EN -> ${PG_HOST}/${DB_NAME}:3000"
exec /usr/local/bin/postgrest
