ARG BUILD_FROM
FROM ${BUILD_FROM}

ARG POSTGREST_VERSION=12.2.3

RUN \
    apk add --no-cache curl xz \
    && curl -fsSL "https://github.com/PostgREST/postgrest/releases/download/v${POSTGREST_VERSION}/postgrest-v${POSTGREST_VERSION}-linux-static-x64.tar.xz" \
      | tar -xJ -C /usr/local/bin \
    && chmod +x /usr/local/bin/postgrest \
    && apk del curl xz

COPY run.sh /
RUN chmod a+x /run.sh

CMD [ "/run.sh" ]
