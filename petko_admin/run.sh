#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

PG_HOST="db21ed7f-postgres-latest"
PORT="8080"

export ADMINER_DEFAULT_SERVER="${PG_HOST}"
export ADMINER_DESIGN="pepa-linha-dark"

bashio::log.info "Petko DB Admin: http://homeassistant.local:${PORT} (or http://192.168.1.6:${PORT})"
bashio::log.info "Login: System=PostgreSQL, Server=${PG_HOST}, User=postgres, Password=<postgres addon password>"
bashio::log.info "Databases: petko_sr (srpski Petko), petko_en (Word Quest EN)"

cd /adminer || exit 1
exec php -S "0.0.0.0:${PORT}" -t /adminer
