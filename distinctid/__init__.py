import calendar
import fcntl
import math
import time
from datetime import date
from pathlib import Path

__author__ = "Chukwudi Nwachukwu"
version = "1.0.2"

URL = "https://github.com/ichux/distinctid"


PATTERN = f"{date.today().year}-01-01 00:00:00"
CURRENT_YEAR = time.strptime(PATTERN, "%Y-%m-%d %H:%M:%S")
CURRENT_OF_EPOCH_YEAR = calendar.timegm(CURRENT_YEAR) * 1000

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
OASIS_FILE = BASE_DIR / ".distinctid.bin"

# create non-existing file
Path(OASIS_FILE).touch()


def distinct(shard_id: int = 1) -> int:
    with open(OASIS_FILE, "r+") as file:
        # Acquire an exclusive lock on the file
        fcntl.flock(file.fileno(), fcntl.LOCK_EX)

        # Increment the ID
        new_id = int(file.read().strip() or 0) + 1

        # Write the new ID back to the file
        file.seek(0)
        file.write(str(new_id))
        file.truncate()

        epoch = math.floor(time.time() * 1000)
        result = (epoch - CURRENT_OF_EPOCH_YEAR) << 23

        did = (result | (shard_id << 10)) | (new_id % 1024)

        # Release the lock
        fcntl.flock(file.fileno(), fcntl.LOCK_UN)
        return did
