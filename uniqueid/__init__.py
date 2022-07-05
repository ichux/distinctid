import calendar
import math
import time
from datetime import date

__author__ = "Chukwudi Nwachukwu"
version = "1.0.0"

URL = "https://github.com/ichux/uniqueid"


PATTERN = f"{date.today().year}-01-01 00:00:00"
CURRENT_YEAR = time.strptime(PATTERN, "%Y-%m-%d %H:%M:%S")
CURRENT_OF_EPOCH_YEAR = calendar.timegm(CURRENT_YEAR) * 1000


def distinct(state: int, shard_id: int = 5) -> int:
    epoch = math.floor(time.time() * 1000)
    result = (epoch - CURRENT_OF_EPOCH_YEAR) << 23
    return (result | (shard_id << 10)) | (state % 1024)
