FROM alpine:3.12 as pkg-builder

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
USER packager

COPY --chown=packager:packager .abuild /home/packager/.abuild/
COPY .abuild/packager-5f82cd49.rsa.pub /etc/apk/keys/
COPY --chown=packager:packager packages/ ./

RUN cd ruby-rubyzip && \
    abuild -r

RUN cd ruby-sablon && \
    abuild -r


FROM alpine:3.12

RUN addgroup --system sablon \
     && adduser --system --ingroup sablon sablon

COPY --from=pkg-builder /home/packager/packages/work/ /packages/
COPY .abuild/packager-5f82cd49.rsa.pub /etc/apk/keys/

RUN apk add --no-cache --repository /packages \
    ruby-sablon \
    py3-aiohttp

CMD ["/bin/sh"]

ENV PYTHONUNBUFFERED 1
WORKDIR /app
USER sablon

EXPOSE 8080

COPY sablon.py .
CMD ["python3", "sablon.py"]
