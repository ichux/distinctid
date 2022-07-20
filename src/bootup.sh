#!/bin/sh
set -e

echo "nameserver 1.1.1.1
nameserver 8.8.8.8
nameserver 8.8.4.4" > /etc/resolv.conf

prime(){
xargs -P 3 -I {} sh -c 'eval "$1"' - {} <<EOF
while ! nc -z localhost 8000; do sleep 0.5; echo "localhost:8000"; done
while ! nc -z localhost 6379; do sleep 0.5; echo "localhost:6379"; done
while ! nc -z localhost 9001; do sleep 0.5; echo "localhost:9001"; done
EOF
}

if [ "$1" = 'daemon' ]; then
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
    prime
fi

exec "$@"
