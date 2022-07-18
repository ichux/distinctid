import os

import redis
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route

from distinctid import distinct

subst = {"host": "localhost", "port": 6379, "db": 0}


async def index(request):
    return JSONResponse(
        {
            "i": distinct(
                redis.StrictRedis(**subst).incr("diid"),
                int(os.getenv("SHARD_ID")),
            )
        }
    )


app = Starlette(routes=[Route("/", index)])
