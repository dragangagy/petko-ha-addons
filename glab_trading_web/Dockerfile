# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.0.0
FROM ${BUILD_FROM}
RUN apk add --no-cache nginx
COPY nginx.conf /etc/nginx/nginx.conf
COPY www /www
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
