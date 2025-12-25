import praw
from datetime import datetime
import logging
from praw import endpoints
import json

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
for logger_name in ("praw", "prawcore"):
	logger = logging.getLogger(logger_name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(handler)

if __name__ == "__main__":
	reddit_watchful = praw.Reddit("Watchful1")
	reddit_bottest = praw.Reddit("Watchful1BotTest")

	response = reddit_watchful.request(method="GET", path="/message/inbox", params={"mark": False, "limit": 100, "show": "all"})
	for message in response['data']['children']:
		print(message['data']['new'])
	print(json.dumps(response, sort_keys=True))
