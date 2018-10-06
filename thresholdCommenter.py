#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import time
import traceback

SUBREDDIT = "sports"
USER_AGENT = "Threshold commenter (by /u/Watchful1)"
SLEEP = 3 * 60 # seconds to sleep between runs
THRESHOLD = 500 # score threshold
COMMENT_TEXT = "This submission has reached the threshold."
LOG_LEVEL = logging.INFO

USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

LOG_FOLDER_NAME = "logs"
if not os.path.exists(LOG_FOLDER_NAME):
	os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 1024 * 16

log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)
if LOG_FILENAME is not None:
	log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME,
	                                                       maxBytes=LOG_FILE_MAXSIZE,
	                                                       backupCount=LOG_FILE_BACKUPCOUNT)
	log_fileHandler.setFormatter(log_formatter)
	log.addHandler(log_fileHandler)


debug = False
user = None
prawIni = False
if len(sys.argv) >= 2:
	user = sys.argv[1]
	for arg in sys.argv:
		if arg == 'debug':
			debug = True
			log.setLevel(logging.DEBUG)
		elif arg == 'prawini':
			prawIni = True


if prawIni:
	if user is None:
		log.error("No user specified, aborting")
		sys.exit(0)
	try:
		r = praw.Reddit(
			user
			, user_agent=USER_AGENT)
	except configparser.NoSectionError:
		log.error(f"User {user} not in praw.ini, aborting")
		sys.exit(0)
else:
	r = praw.Reddit(
		username=USERNAME
		,password=PASSWORD
		,client_id=CLIENT_ID
		,client_secret=CLIENT_SECRET
		,user_agent=USER_AGENT)

log.info("Logged into reddit as /u/{}".format(str(r.user.me())))

while True:
	try:
		startTime = time.perf_counter()
		log.debug("Starting run")

		for submission in r.subreddit(SUBREDDIT).hot():
			if submission.score > THRESHOLD and not submission.saved:
				log.info(f"Replying to submission that is past the threshold: {submission.id}")
				comment = submission.reply(COMMENT_TEXT)
				comment.mod.distinguish(how='yes', sticky=True)
				comment.disable_inbox_replies()
				submission.save()

		log.debug("Run complete in %d seconds", int(time.perf_counter() - startTime))
	except Exception as err:
		log.warning("Hit an error in main loop")
		log.warning(traceback.format_exc())

	time.sleep(SLEEP)
