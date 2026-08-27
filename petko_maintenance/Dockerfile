# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.0.0
FROM ${BUILD_FROM}
RUN apk add --no-cache postgresql-client
COPY sql/ /sql/
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
