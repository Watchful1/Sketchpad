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

USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

flair_config = {
	'oldFlair1': 'newFlair1',
	'oldFlair2': 'newFlair2',
	'oldFlair3': 'newFlair3',
}

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
		elif arg == 'prawini':
			prawIni = True
else:
	log.error("No user specified, aborting")
	sys.exit(0)


if prawIni:
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

try:
	sub = r.subreddit(SUBREDDIT)
	startTime = time.perf_counter()

	numFlairs = 0
	flair_map = []
	for flair in sub.flair(limit=None):
		numFlairs += 1

		if flair['flair_text'] in flair_config:
			item = {
				'user': flair['user'].name,
				'flair_text': flair_config[flair['flair_text']]
			}
			flair_map.append(item)
			log.info("/u/%s from '%s' to '%s'", flair['user'].name, flair['flair_text'], flair_config[flair['flair_text']])
		else:
			log.debug("/u/%s unchanged from '%s'", flair['user'].name, flair['flair_text'])

	log.info("Found %d flairs in %d seconds", numFlairs, int(time.perf_counter() - startTime))
	startTime = time.perf_counter()
	log.info("Updating %d flairs. Running update function, this could take a while.", len(flair_map))
	sub.flair.update(flair_map)
	log.info("Done in %d seconds", int(time.perf_counter() - startTime))
except Exception as err:
	log.warning("Hit an error in main loop")
	log.warning(traceback.format_exc())
