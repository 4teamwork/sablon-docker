FROM alpine:3.16 as pkg-builder

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

RUN cd ruby-rubyzip && \
    abuild -r

RUN cd ruby-sablon && \
    abuild -r


FROM alpine:3.16

RUN addgroup --system sablon \
     && adduser --system --ingroup sablon sablon

COPY --from=pkg-builder /home/packager/packages/work/ /packages/
COPY --from=pkg-builder /home/packager/.abuild/*.pub /etc/apk/keys/

RUN apk add --no-cache --repository /packages \
    ruby-sablon \
    py3-aiohttp

ENV PYTHONUNBUFFERED 1
WORKDIR /app
USER sablon

EXPOSE 8080

COPY sablon.py .
CMD ["python3", "sablon.py"]
