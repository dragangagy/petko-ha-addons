# syntax=docker/dockerfile:1
ARG BUILD_FROM=ghcr.io/hassio-addons/base:16.0.0
FROM ngrok/ngrok:latest AS ngrok
FROM ${BUILD_FROM}
RUN apk add --no-cache nginx
COPY --from=ngrok /bin/ngrok /usr/local/bin/ngrok
COPY nginx.conf /etc/nginx/nginx.conf
COPY run.sh /
RUN chmod a+x /run.sh
CMD [ "/run.sh" ]
