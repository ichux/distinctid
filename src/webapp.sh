#!/bin/sh
set -e

cd /bin && exec gunicorn scale:app --worker-class $GUNICORN_WORKERS \
	-k uvicorn.workers.UvicornWorker \
	--bind 0.0.0.0:8000
