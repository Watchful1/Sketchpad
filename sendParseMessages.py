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


# log = logging.getLogger("bot")
# log.setLevel(logging.INFO)
# log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
# log_stderrHandler = logging.StreamHandler()
# log_stderrHandler.setFormatter(log_formatter)
# log.addHandler(log_stderrHandler)

if __name__ == "__main__":
	reddit_watchful = praw.Reddit("Watchful1")
	reddit_bottest = praw.Reddit("Watchful1BotTest")
	reddit_botslave = praw.Reddit("TestBotSlave1")

	run_number = 3
	num_messages_per_target = 500

	# targets = [
	# 	"TestBotSlave1",
	# 	"TestBotSlave2",
	# 	"TestBotSlave3",
	# 	"TestBotSlave4",
	# 	"TestBotSlave5",
	# ]
	#
	# successes = 0
	# failures = 0
	# for i in range(num_messages_per_target):
	# 	for target in targets:
	# 		try:
	# 			log.info(f"{i}|{successes}|{failures}: Sending {target}")
	# 			reddit_bottest.redditor(target).message("test subject", f"from u/Watchful1BotTest to u/{target} : {run_number} : {i}")
	# 			log.info(f"{i}|{successes}|{failures}: Success {target}")
	# 			successes += 1
	# 		except Exception as e:
	# 			failures += 1
	# 			log.info(f"{i}|{successes}|{failures}: Failure {target}")
	# 			log.info(e)
		# if i % 10 == 0:
		# 	log.info(f"{i} | {successes} | {failures}")




	try:
		reddit_watchful.redditor("TestBotSlave1").message("test subject", f"from u/Watchful1 to u/TestBotSlave1 : {run_number}")
	except Exception as e:
		logger.info(e)
	try:
		reddit_watchful.redditor("Watchful1BotTest").message("test subject", f"from u/Watchful1 to u/Watchful1BotTest : {run_number}")
	except Exception as e:
		logger.info(e)

	try:
		reddit_bottest.redditor("Watchful1").message("test subject", f"from u/Watchful1BotTest to u/Watchful1 : {run_number}")
	except Exception as e:
		logger.info(e)
	try:
		reddit_bottest.redditor("TestBotSlave1").message("test subject", f"from u/Watchful1BotTest to u/TestBotSlave1 : {run_number}")
	except Exception as e:
		logger.info(e)

	try:
		reddit_botslave.redditor("Watchful1").message("test subject", f"from u/TestBotSlave1 to u/Watchful1 : {run_number}")
	except Exception as e:
		logger.info(e)
	try:
		reddit_botslave.redditor("Watchful1BotTest").message("test subject", f"from u/TestBotSlave1 to u/Watchful1BotTest : {run_number}")
	except Exception as e:
		logger.info(e)

	try:
		for message in reddit_bottest.inbox.all(limit=5):
			print(f"{message.author.name} : {message.subject} : {message.body}")
	except Exception as e:
		logger.info(e)

	try:
		for message in reddit_botslave.inbox.all(limit=5):
			print(f"{message.author.name} : {message.subject} : {message.body}")
	except Exception as e:
		logger.info(e)

	# Watchful1 -> Watchful1BotTest | Success | message -> message
	# Watchful1 -> TestBotSlave1 | Success | message -> message
	# Watchful1BotTest -> Watchful1 | Failed 400 http response
	# Watchful1BotTest -> TestBotSlave1 | Failed 400 http response
	# TestBotSlave1 -> Watchful1 | Success | message -> message
	# TestBotSlave1 -> Watchful1BotTest | Success | chat -> chat

	# Fetching: POST https://oauth.reddit.com/api/compose/
	# Data: [('api_type', 'json'), ('subject', 'test subject'), ('text', 'test message'), ('to', 'Watchful1')]
	# Params: {'raw_json': 1}

	# Accessing the message inbox on TestBotSlave1 returns normal private messages
	# Accessing the message inbox on Watchful1BotTest fails with http 400

	# Fetching: GET https://oauth.reddit.com/message/inbox/
	# Data: None
	# Params: {'limit': 1024, 'raw_json': 1}

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




	#response = reddit_bottest.request(method="GET", path=endpoints.API_PATH["info"], params={"id": id_string})
	# response = reddit_bottest._core._request_with_retries(data=None, files=None, json=None, method="GET", params=None, timeout=16, url="https://oauth.reddit.com/message/inbox/")
	# print(response['data']['children'])
