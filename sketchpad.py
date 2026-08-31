import praw
from datetime import datetime
import logging
from praw import endpoints
import json

# handler = logging.StreamHandler()
# handler.setLevel(logging.DEBUG)
# for logger_name in ("praw", "prawcore"):
# 	logger = logging.getLogger(logger_name)
# 	logger.setLevel(logging.DEBUG)
# 	logger.addHandler(handler)

if __name__ == "__main__":
	reddit_watchful = praw.Reddit("Watchful1")
	#reddit_bottest = praw.Reddit("Watchful1BotTest")

	reddit_watchful.redditor("updateme-dev").message(subject="test",message="spike 11")

	#https://www.reddit.com/r/OUTFITS/comments/1t491dn/is_this_outfit_too_revealing_for_class.json
	# submission = reddit_watchful.submission("1t491dn")
	# submission._fetch()
	# print(submission.author.name)