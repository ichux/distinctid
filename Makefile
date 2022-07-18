# Do not remove this block. It is used by the 'help' rule when
# constructing the help output.
# help:
# help: UniqueID help
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
	@docker logs --follow cuid

.PHONY: sh
# help: sh 				- sh for the container
sh:
	@docker exec -it cuid sh

.PHONY: nid
# help: nid 				- next id
nid:
	@docker exec -it cuid python3 -c \
	'import redis; print(\
	redis.StrictRedis(host="localhost", port=6379, db=0).incr("diid")\
	)'
