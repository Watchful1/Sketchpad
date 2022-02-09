import praw
from datetime import datetime


reddit = praw.Reddit("Watchful1")

flairs = reddit.post("r/SubTestBot2/api/flairselector/", data={"is_newlink": True})["choices"]

print("")
