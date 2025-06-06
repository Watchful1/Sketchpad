import praw
from datetime import datetime
import logging
from praw import endpoints

handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
for logger_name in ("praw", "prawcore"):
	logger = logging.getLogger(logger_name)
	logger.setLevel(logging.DEBUG)
	logger.addHandler(handler)

if __name__ == "__main__":
	reddit_watchful = praw.Reddit("Watchful1")
	reddit_bottest = praw.Reddit("Watchful1BotTest")

	# compose message
	# mark read
	# inbox
	# unread inbox
	# stream inbox

	# id of sent messages
	# links to old system messages
	# comment replies in inbox
	# limits, multisend endpoint
	# message/mentions and mentions in general




	# response = reddit.request(method="GET", path=endpoints.API_PATH["info"], params={"id": id_string})
	# print(response['data']['children'])
