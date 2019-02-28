#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser

USER_AGENT = "Mod Log Parser (by /u/Watchful1)"
LOG_LEVEL = logging.INFO


SUBREDDIT = "CompetitiveOverwatch"
INFRACTIONS_LIMIT = 3
DAYS_OLD_TO_CLEAR = 30
REMOVAL_REASON = "douchebaggary/slur"


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

user = None
if len(sys.argv) >= 2:
	user = sys.argv[1]
else:
	log.error("No user specified, aborting")
	sys.exit(0)

try:
	r = praw.Reddit(
		user
		,user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error(f"User {user} not in praw.ini, aborting")
	sys.exit(0)

removed_ids = []
for log_object in r.subreddit(SUBREDDIT).mod.log(action="removelink", limit=10000):
	removed_ids.append(log_object.target_fullname)

log.info(f"Found {len(removed_ids)} removed posts")

removed_clip_ids = []
for post in r.info(removed_ids):
	if post.domain == "clips.twitch.tv":
		log.info(f"https://old.reddit.com{post.permalink}")
		removed_clip_ids.append(post.name)

log.info(f"Found {len(removed_clip_ids)} removed clips")
