# Sample HTTP in Alpine Linux
Serve the root directory inside a docker container

```bash
cp example.env .env && gsed -i 's/JSON_RESPONSE.*/JSON_RESPONSE\=true/' .env
make build

cp example.env .env && gsed -i 's/JSON_RESPONSE.*/JSON_RESPONSE\=false/' .env
make build

# JSON_RESPONSE=true. Where 18080 is 'WEB_IP' as found in .env
xargs -P 3 -I {} sh -c 'eval "$1"' - {} <<EOF
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
curl 127.0.0.1:18080 && echo
EOF

# https://scoutapm.com/blog/how-to-use-docker-healthcheck

# docker network create nc_network
# networks:
#   default:
#     name: nc_network

# networks:
#   gateway: {}
```
