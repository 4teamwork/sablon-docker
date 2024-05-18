FROM alpine:3.19 as alpine-upgrader
RUN apk upgrade --no-cache

FROM scratch as alpine-upgraded
COPY --from=alpine-upgrader / /
CMD ["/bin/sh"]

FROM alpine-upgraded as pkg-builder

RUN apk -U add \
    sudo \
    alpine-sdk \
    ruby-dev

RUN mkdir -p /var/cache/distfiles && \
    adduser -D packager && \
    addgroup packager abuild && \
    chgrp abuild /var/cache/distfiles && \
    chmod g+w /var/cache/distfiles && \
    echo "packager ALL=(ALL) NOPASSWD: ALL" >> /etc/sudoers

WORKDIR /work
RUN chown packager /work
USER packager

RUN abuild-keygen -a -i -n

COPY --chown=packager:packager packages/ ./

RUN cd ruby-xml-simple && \
    abuild -r

RUN cd ruby-rubyzip && \
    abuild -r

RUN cd ruby-sablon && \
    abuild -r


FROM alpine-upgraded

RUN addgroup --system sablon \
     && adduser --system --ingroup sablon sablon

RUN --mount=from=pkg-builder,source=/home/packager/packages/work,target=/packages \
    --mount=from=pkg-builder,source=/etc/apk/keys,target=/etc/apk/keys \
    apk add --no-cache --repository /packages \
    ruby-sablon \
    py3-aiohttp

ENV PYTHONUNBUFFERED 1
WORKDIR /app
USER sablon

EXPOSE 8080

COPY sablon.py .
CMD ["python3", "sablon.py"]
