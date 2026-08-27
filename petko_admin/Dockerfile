# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.0.0
FROM adminer:4.8.1 AS adminer_src
FROM ${BUILD_FROM}
RUN apk add --no-cache php83-cli php83-session php83-pdo_pgsql php83-openssl
COPY --from=adminer_src /var/www/html /adminer
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
