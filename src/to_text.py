import os

import redis
from starlette.responses import PlainTextResponse

from distinctid import distinct

subst = {"host": "localhost", "port": 6379, "db": 0}


async def app(scope, receive, send):
    assert scope["type"] == "http"
    response = PlainTextResponse(
        str(
            distinct(
                redis.StrictRedis(**subst).incr("distinctid"),
                int(os.getenv("SHARD_ID")),
            )
        )
    )
    await response(scope, receive, send)
