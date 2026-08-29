#!/usr/bin/with-contenv bashio
# shellcheck shell=bash

TOKEN="$(bashio::config 'token')"

if [[ -z "${TOKEN}" ]]; then
  bashio::log.fatal "Cloudflare tunnel token nije podešen."
  bashio::log.fatal "Kreiraj tunel u Cloudflare Zero Trust i nalepi token u add-on konfiguraciju."
  exit 1
fi

bashio::log.info "Starting Cloudflare Tunnel (host network -> 127.0.0.1:3000 / :3001, protocol http2)"
exec cloudflared tunnel run --protocol http2 --token "${TOKEN}"
