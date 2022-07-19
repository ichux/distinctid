#!/bin/sh

cd /bin

echo -e "\nJSON_RESPONSE = $JSON_RESPONSE\n"

if [[ $JSON_RESPONSE == "true" ]]; then
	exec gunicorn to_json:app --worker-class $GUNICORN_WORKERS \
		-k uvicorn.workers.UvicornWorker \
		--bind 0.0.0.0:8000
fi


if [[ $JSON_RESPONSE == "false" ]]; then
	exec gunicorn to_text:app --worker-class $GUNICORN_WORKERS \
		-k uvicorn.workers.UvicornWorker \
		--bind 0.0.0.0:8000
fi

echo "options: 'true' or 'false'" && exit
