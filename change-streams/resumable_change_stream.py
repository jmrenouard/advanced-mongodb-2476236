import os
import pymongo
import time
from bson.json_util import dumps


def run_change_stream(client, resume_token=None, sleep=1):
    """Watch collection iteratively, resuming with exponential backoff on transient errors."""
    while True:
        try:
            watch_kwargs = {"resume_after": resume_token} if resume_token is not None else {}
            with client.changestream.collection.watch(**watch_kwargs) as stream:
                for change in stream:
                    print(dumps(change))
                    print('')  # for readability only
                    resume_token = stream.resume_token
                    sleep = 1
        except pymongo.errors.PyMongoError:
            # Stop if initialization failed before receiving any resume token.
            if resume_token is None:
                print("unrecoverable error")
                return
            time.sleep(sleep)
            sleep = min(sleep * 2, 60)


def main():
    client = pymongo.MongoClient(os.environ['CHANGE_STREAM_DB'])
    run_change_stream(client, None, 1)


if __name__ == "__main__":
    main()
