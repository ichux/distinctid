#!/bin/bash

if ! command -v openssl &> /dev/null; then
    echo "'openssl' could not be found. Please install it"
    exit 0
else
    if [ ! $1 ]; then
        echo "Usage: 'source filename.sh password'"
    else
        # http://supervisord.org/configuration.html#unix_http_server
        if [ "$(uname)" == "Darwin" ]; then
            printf $1 | openssl dgst -sha1 | xargs -I RESPONSE echo "{SHA}"RESPONSE
        else
            printf $1 | openssl dgst -sha1 | xargs -iRESPONSE echo "{SHA}"RESPONSE
        fi
    fi
fi
