import os

import redis
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Route
from uvicorn.workers import UvicornWorker

from distinctid import distinct


class DistinctIDUvicornWorker(UvicornWorker):
    CONFIG_KWARGS = {
        "loop": "auto",
        "http": "auto",
        "date_header": False,
        "server_header": False,
    }


subst = {"host": "localhost", "port": 6379, "db": 0}


async def index(request):
    return JSONResponse(
        distinct(
            redis.StrictRedis(**subst).incr("distinctid"),
            int(os.getenv("SHARD_ID")),
        )
    )


app = Starlette(routes=[Route("/", index)])
