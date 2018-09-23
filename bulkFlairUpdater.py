#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import signal
import time
import traceback

SUBREDDIT = "SubTestBot1"
USER_AGENT = "Bulk flair updater (by /u/Watchful1)"
REDDIT_OWNER = "Watchful1"
LOG_LEVEL = logging.INFO


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
if len(sys.argv) >= 2:
	user = sys.argv[1]
	for arg in sys.argv:
		if arg == 'debug':
			debug = True
else:
	log.error("No user specified, aborting")
	sys.exit(0)


try:
	r = praw.Reddit(
		user
		,user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error("User "+user+" not in praw.ini, aborting")
	sys.exit(0)

log.info("Logged into reddit as /u/{}".format(str(r.user.me())))

try:
	sub = r.subreddit(SUBREDDIT)
	startTime = time.perf_counter()
	flairTypes = set()
	numFlairs = 0
	for flair in sub.flair(limit=None):
		log.debug(flair)
		flairTypes.add(flair['flair_text'])
		numFlairs += 1

	log.info("Found %d flairs, %d unique, in %d seconds", numFlairs, len(flairTypes), int(time.perf_counter() - startTime))

except Exception as err:
	log.warning("Hit an error in main loop")
	log.warning(traceback.format_exc())
