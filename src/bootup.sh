#!/bin/sh
set -e

echo "nameserver 1.1.1.1
nameserver 8.8.8.8
nameserver 8.8.4.4" > /etc/resolv.conf

if [ "$1" = 'daemon' ]; then
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf

    # prime essential ports
    while ! nc -z localhost 8000; do sleep 0.5; echo "localhost:8000"; done
    while ! nc -z localhost 6379; do sleep 0.5; echo "localhost:6379"; done
    while ! nc -z localhost 9001; do sleep 0.5; echo "localhost:9001"; done
fi

exec "$@"
