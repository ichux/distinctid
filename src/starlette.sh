#!/bin/sh

cd /bin

if [ ! $SCALE_WORKERS ]; then
	SCALE_WORKERS=2
else
	if [ $SCALE_WORKERS -gt 5 ]; then
		SCALE_WORKERS=5
	fi
fi

echo -e "\nSCALE_WORKERS == $SCALE_WORKERS\nNPROC         == `nproc`\n"

exec gunicorn diid:app \
	--workers $(($SCALE_WORKERS * `nproc`)) \
	--worker-class diid.DistinctIDUvicornWorker \
	--bind unix:/bin/gunicorn.sock \
	--bind 0.0.0.0:8000
