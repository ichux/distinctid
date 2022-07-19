# Sample HTTP in Alpine Linux
Serve the root directory inside a docker container

```bash
cp example.env .env

# JSON_RESPONSE=true. Where 18080 is 'WEB_IP' as found in .env
curl -s 127.0.0.1:18080 | py3 -mjson.tool

# JSON_RESPONSE=false. Where 18080 is 'WEB_IP' as found in .env
curl 127.0.0.1:18080

# https://scoutapm.com/blog/how-to-use-docker-healthcheck

# docker network create nc_network
# networks:
#   default:
#     name: nc_network

# networks:
#   gateway: {}
```