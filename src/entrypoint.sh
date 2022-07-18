#!/bin/sh
set -e

echo "nameserver 1.1.1.1
nameserver 8.8.8.8
nameserver 8.8.4.4" > /etc/resolv.conf

if [ "$1" = 'daemon' ]; then
    exec /usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
fi

exec "$@"
