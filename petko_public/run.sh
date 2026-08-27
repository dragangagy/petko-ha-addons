#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

TOKEN="$(bashio::config 'ngrok_authtoken')"
DOMAIN="$(bashio::config 'ngrok_domain')"

if [[ -z "${TOKEN}" || -z "${DOMAIN}" ]]; then
  bashio::log.fatal "ngrok_authtoken i ngrok_domain moraju biti podeseni."
  bashio::log.fatal "Besplatno: https://dashboard.ngrok.com/signup"
  exit 1
fi

bashio::log.info "Starting nginx proxy on 127.0.0.1:3099 (/en -> :3000, /sr -> :3001)"
nginx -c /etc/nginx/nginx.conf

bashio::log.info "Public EN: https://${DOMAIN}/en/"
bashio::log.info "Public SR: https://${DOMAIN}/sr/"
exec ngrok http --authtoken="${TOKEN}" --domain="${DOMAIN}" http://127.0.0.1:3099
