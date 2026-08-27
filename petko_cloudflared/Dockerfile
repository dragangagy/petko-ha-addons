# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.0.0
FROM cloudflare/cloudflared:2025.2.1 AS cloudflared
FROM ${BUILD_FROM}
COPY --from=cloudflared /usr/local/bin/cloudflared /usr/local/bin/cloudflared
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
