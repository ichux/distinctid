# How to scale distinctid
```bash

# spin up a network
docker network create --driver=bridge --internal netdiid

# spin up containers
docker run -d \
   --name web1 --net netdiid jmalloc/echo-server:latest
   
docker run -d \
   --name web2 --net netdiid jmalloc/echo-server:latest
   
docker run -d \
   --name web3 --net netdiid jmalloc/echo-server:latest

# haproxy.cfg
global
  stats socket /var/run/api.sock user haproxy group haproxy mode 660 level admin expose-fd listeners
  log stdout format raw local0 info

defaults
  mode http
  timeout client 10s
  timeout connect 5s
  timeout server 10s
  timeout http-request 10s
  log global

frontend stats
  bind *:8404
  stats enable
  stats uri /
  stats refresh 10s

frontend myfrontend
  bind :80
  default_backend webservers

backend webservers
  server s1 web1:8080 check
  server s2 web2:8080 check
  server s3 web3:8080 check

# start haproxy
docker run -d \
   --name haproxy \
   --net netdiid \
   -v $(pwd):/usr/local/etc/haproxy:ro \
   -p 80:80 \
   -p 8404:8404 \
   haproxytech/haproxy-alpine:2.4

# kill haproxy to restart, in case of a config change
docker kill -s HUP haproxy

# clean up
docker stop web1 && docker rm web1
docker stop web2 && docker rm web2
docker stop web3 && docker rm web3
docker stop haproxy && docker rm haproxy
docker network rm netdiid

# docker-compose up -d --scale service1=5 --scale service2=6
# https://www.haproxy.com/blog/how-to-run-haproxy-with-docker/
```