#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import time
from datetime import datetime

USER_AGENT = "Mod Log Downloader (by /u/Watchful1)"
LOG_LEVEL = logging.INFO

SUBREDDIT = "CompetitiveOverwatch"
FILE_NAME = "modlog.txt"

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
	log_fileHandler = logging.handlers.RotatingFileHandler(
		LOG_FILENAME,
	    maxBytes=LOG_FILE_MAXSIZE,
	    backupCount=LOG_FILE_BACKUPCOUNT)
	log_fileHandler.setFormatter(log_formatter)
	log.addHandler(log_fileHandler)


def convert_test(str):
	return str.encode(encoding='ascii', errors='ignore').decode()


user = None
if len(sys.argv) >= 2:
	user = sys.argv[1]

try:
	r = praw.Reddit(
		user
		, user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error(f"User {user} not in praw.ini, aborting")
	sys.exit(0)

log.info("Logged into reddit as /u/{}".format(str(r.user.me())))

startTime = time.perf_counter()

log.debug("Starting run")

handle = open(FILE_NAME, 'w')
logs_parsed = 0
for mod_log in r.subreddit(SUBREDDIT).mod.log(limit=None):
	logs_parsed += 1
	logDatetime = datetime.utcfromtimestamp(mod_log.created_utc)

	handle.write(mod_log.target_author.ljust(20))
	handle.write(mod_log.action.ljust(20))
	handle.write(logDatetime.strftime('%Y-%m-%d %H:%M:%S').ljust(22))
	if mod_log.target_permalink is not None:
		handle.write(f"https://www.reddit.com{convert_test(mod_log.target_permalink)}")

	handle.write("\n")

	if logs_parsed % 1000 == 0:
		log.info(f"{logs_parsed} : {logDatetime.strftime('%Y-%m-%d %H:%M:%S')}")

log.debug("Run complete after: %d", int(time.perf_counter() - startTime))

handle.close()
