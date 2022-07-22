# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: DistinctID help
# help:

.PHONY: help
# help: help				- Please use "make <target>" where <target> is one of
help:
	@grep "^# help\:" Makefile | sed 's/\# help\: //' | sed 's/\# help\://'

.PHONY: build
# help: build 				- Build the image
build:
	@echo "Y" | docker builder prune
	@docker-compose up --detach --build

.PHONY: log
# help: log 				- Container logs
log:
	@docker logs --follow c_diid

.PHONY: sh
# help: sh 				- sh for the container
sh:
	@docker exec -it c_diid sh

.PHONY: nid
# help: nid 				- next id
nid:
	@docker exec -it c_diid python3 -c \
	'import redis; print(\
	redis.StrictRedis(host="localhost", port=6379, db=0).incr("diid")\
	)'

.PHONY: ms
# help: ms 				- make a sock
ms:
	@python3 -c "import socket as s, os; \
	sock = s.socket(s.AF_UNIX); sock.bind('gunicorn.sock'); \
	os.chmod('gunicorn.sock', 0o777)"

.PHONY: sock
# help: sock 				- cp a sock
sock:
	@docker cp c_diid:/bin/gunicorn.sock gunicorn.sock
