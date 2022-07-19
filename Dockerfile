FROM alpine:edge

# Install packages
RUN apk add --update --no-cache curl py-pip python3 redis supervisor \
    netcat-openbsd && pip install --no-cache-dir redis \
    distinctid starlette uvicorn gunicorn && apk del --purge py-pip && \
    mkdir -p /etc/redis /var/redis etc/supervisor/conf.d

ADD src /srcfiles
WORKDIR /srcfiles

RUN mv supervisord.conf /etc/supervisor/conf.d && \
    mv redis.conf /etc/redis \
    && chmod +x bootup.sh && mv bootup.sh /bin \
    && chmod +x starlette.sh && mv starlette.sh /bin \
    && mv to_json.py /bin && mv to_text.py /bin

EXPOSE 8000 6379 9001

ENTRYPOINT ["sh", "/bin/bootup.sh"]
