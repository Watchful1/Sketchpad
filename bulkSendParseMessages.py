import praw
from datetime import datetime
import logging
from praw import endpoints



log = logging.getLogger("bot")
log.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)

if __name__ == "__main__":
	reddit_watchful = praw.Reddit("Watchful1")
	reddit_bottest = praw.Reddit("Watchful1BotTest")
	reddit_botslave = praw.Reddit("TestBotSlave1")

	run_number = 4
	num_messages_per_target = 500

	targets = [
		"TestBotSlave1",
		"TestBotSlave2",
		"TestBotSlave3",
		"TestBotSlave4",
		"TestBotSlave5",
	]

	successes = 0
	failures = 0
	for i in range(num_messages_per_target):
		for target in targets:
			try:
				log.info(f"{i}|{successes}|{failures}: Sending {target}")
				reddit_bottest.redditor(target).message("test subject", f"from u/Watchful1BotTest to u/{target} : {run_number} : {i}")
				log.info(f"{i}|{successes}|{failures}: Success {target}")
				successes += 1
			except Exception as e:
				failures += 1
				log.info(f"{i}|{successes}|{failures}: Failure {target}")
				log.info(e)
		# if i % 10 == 0:
		# 	log.info(f"{i} | {successes} | {failures}")

