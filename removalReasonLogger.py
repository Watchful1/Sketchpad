#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
from datetime import datetime

USER_AGENT = "Mod Log Parser (by /u/Watchful1)"
LOG_LEVEL = logging.INFO


SUBREDDIT = "CompetitiveOverwatch"


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
	if log_object.mod != "AutoModerator" and log_object.details == "remove":
		submission = r.submission(log_object.target_fullname[3:])
		if len(submission.comments):
			comment = submission.comments[0]
			if comment is not None and comment.author is not None and comment.author.name == log_object.mod.name and \
				"Low effort content can flood the subreddit and drown out meaningful discussion, and is thus not allowed" in comment.body:
				log.info(f"{log_object.mod.name.ljust(14)} : {datetime.utcfromtimestamp(log_object.created_utc).strftime('%Y-%m-%d')} : https://old.reddit.com{submission.permalink}")
