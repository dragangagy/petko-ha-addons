# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.0.0
FROM postgrest/postgrest:v12.2.3 AS postgrest
FROM ${BUILD_FROM}
COPY --from=postgrest /bin/postgrest /usr/local/bin/postgrest
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
