# DISTINCTID
With `distinctid`, you can generate distinct/unique IDs. Just think of it as something that can replace your UUID. It has the advantage of being a long integer and can be sorted in ASC or DESC order.

# Philosophy
This code is pure Python and relies on [this article](https://instagram-engineering.com/sharding-ids-at-instagram-1cf5a71e5a5c) which led to [this](https://gist.github.com/ichux/1b5d15129370341811fb12eb7e333917), [this](https://github.com/ichux/postgresql-id-shard) and this present project you are reading now.

# 100% Unittest Coverage
See the unittest to know how to use it

```bash
pip install coverage

# unittest
python -m unittest discover

# OR

# coverage with unittest
coverage run -m unittest discover \
    && coverage html && coverage report

# browse: htmlcov/index.html 
```

# How to Use
```bash
# Browse a short video:
# https://twitter.com/zuoike/status/1544337418467397633

cp example.env .env # && gsed -i 's/JSON_RESPONSE.*/JSON_RESPONSE\=true/' .env
make build

# Run 100 calls!
# Where 18080 is 'WEB_IP' as found in .env
eval "
$(cat <<EOF                                       
for i in {1..100}; do echo 'curl -s 127.0.0.1:18080'; done
EOF
)" | xargs -P 20 -I {} sh -c 'printf "`$1`\n"' - {}
```