#!/usr/bin/with-contenv bashio
# shellcheck shell=bash
set -euo pipefail
bashio::log.info "Starting G-Lab Trading Web on :3010"
exec nginx -c /etc/nginx/nginx.conf -g 'daemon off;'
