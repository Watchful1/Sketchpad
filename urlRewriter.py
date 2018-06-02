#!/usr/bin/python3

import os
import logging.handlers
import traceback
import re
import configparser
import praw
import sys
import time
from datetime import datetime

### Config
SUBREDDIT = "subtestbot1"
USERNAME = "Watchful1BotTest"
OWNER = "Watchful1"
USER_AGENT = "Url bot (by /u/Watchful1)"
ONCE = False

### Logging setup
# this is a bunch of standard logging setup I copy to each project of mine. Just makes it easy to log stuff to both
# console and a file as well as rotating the log files if they get too big
LOG_FOLDER_NAME = "logs"
LOG_LEVEL = logging.DEBUG
if not os.path.exists(LOG_FOLDER_NAME):
	os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 256 * 16

log = logging.getLogger("bot")
log.setLevel(LOG_LEVEL)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_stderrHandler = logging.StreamHandler()
log_stderrHandler.setFormatter(log_formatter)
log.addHandler(log_stderrHandler)
if LOG_FILENAME is not None:
	log_fileHandler = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=LOG_FILE_MAXSIZE, backupCount=LOG_FILE_BACKUPCOUNT)
	log_formatter_file = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
	log_fileHandler.setFormatter(log_formatter_file)
	log.addHandler(log_fileHandler)


def getLinks(text):
	links = re.findall('(?:dispatch.com)([^ \]\[\n]{5,250})', text)
	updatedLinks = []
	for link in links:
		log.debug("Link: {}".format(link))
		updatedLinks.append("http://www.thisweeknews.com{}".format(link))
	return updatedLinks


def getText(links, isSubmission):
	bldr = []
	bldr.append("This ")
	if isSubmission:
		bldr.append("submission")
	else:
		bldr.append("comment")
	bldr.append(" has ")
	if len(links) > 1:
		bldr.append("links")
	else:
		bldr.append("a link")
	bldr.append(" to dispatch.com, which has a paywall. You can instead use the following ")
	if len(links) > 1:
		bldr.append("links")
	else:
		bldr.append("link")
	bldr.append(" to access the article for free.")
	bldr.append("\n\n")

	for link in links:
		bldr.append(link)
		bldr.append("  \n")

	bldr.append("\n")

	footer = "this is a bot and this action was performed automatically. If something's wrong, contact /u/{}".format(OWNER)
	bldr.append("^^{}".format(' ^^'.join(footer.split(" "))))

	return ''.join(bldr)


try:
	reddit = praw.Reddit(
		USERNAME
		,user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error("User "+USERNAME+" not in praw.ini, aborting")
	sys.exit(0)

recentSubmission = datetime.utcnow()
recentComment = datetime.utcnow()

while True:
	log.debug("Starting run: {} : {}".format(recentSubmission.strftime("%m/%d/%y %H:%M:%S"), recentComment.strftime("%m/%d/%y %H:%M:%S")))
	try:
		sub = reddit.subreddit(SUBREDDIT)

		submissions = []
		for submission in sub.new():
			if datetime.utcfromtimestamp(submission.created_utc) < recentSubmission:
				break

			submissions.append(submission)

		for submission in submissions[::-1]:
			log.info("Processing submission: {}".format(submission.id))
			recentSubmission = datetime.utcfromtimestamp(submission.created_utc + 1)
			if submission.is_self:
				links = getLinks(submission.selftext)
				if len(links) > 0:
					log.info("Found self post links, replying: {}".format(submission.id))
					message = getText(links, True)
					submission.reply(message)
			else:
				links = getLinks(submission.url)
				if len(links) > 0:
					log.info("Found link, replying: {}".format(submission.id))
					message = getText(links, True)
					submission.reply(message)

		comments = []
		for comment in sub.comments():
			if datetime.utcfromtimestamp(comment.created_utc) < recentComment:
				break

			comments.append(comment)

		for comment in comments[::-1]:
			log.info("Processing comment: {}".format(comment.id))
			recentComment = datetime.utcfromtimestamp(comment.created_utc + 1)
			links = getLinks(comment.body)
			if len(links) > 0:
				log.info("Found link in comment, replying: {}".format(comment.id))
				message = getText(links, False)
				comment.reply(message)
	except Exception as err:
		log.warning("Hit an error in main loop")
		log.warning(traceback.format_exc())

	log.debug("Run complete")

	if ONCE:
		break

	time.sleep(5)
