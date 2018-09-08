#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import signal
import time
import traceback
import sqlite3
import re
from shutil import copyfile
from datetime import datetime
from datetime import timedelta

### Config ###
LOG_FOLDER_NAME = "logs"
SUBREDDIT = "subtestbot1"
USER_AGENT = "Comment locker (by /u/Watchful1)"
LOOP_TIME = 5 * 60
DATABASE_NAME = "database.db"
LOG_LEVEL = logging.INFO

USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

### Logging setup ###
if not os.path.exists(LOG_FOLDER_NAME):
	os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME+"/"+"bot.log"
LOG_FILE_BACKUPCOUNT = 5
LOG_FILE_MAXSIZE = 1024 * 256 * 64

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


def signal_handler(signal, frame):
	log.info("Handling interrupt")
	dbConn.commit()
	dbConn.close()
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


dbConn = sqlite3.connect(DATABASE_NAME)
c = dbConn.cursor()
c.execute('''
	CREATE TABLE IF NOT EXISTS locked (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		CommentID VARCHAR(10) NOT NULL,
		UNIQUE (CommentID)
	)
''')
dbConn.commit()


def addComment(commentID):
	c = dbConn.cursor()
	try:
		c.execute('''
			INSERT INTO locked
			(CommentID)
			VALUES (?)
		''', (commentID,))
	except sqlite3.IntegrityError:
		return False

	dbConn.commit()
	return True


def removeComment(commentID):
	c = dbConn.cursor()
	c.execute('''
		DELETE FROM locked
		WHERE CommentID = ?
	''', (commentID,))
	dbConn.commit()

	if c.rowcount == 1:
		return True
	else:
		return False


def isCommentLocked(commentID):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT CommentID
		FROM locked
		WHERE CommentID = ?
	''', (commentID,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return False
	else:
		return True


def getIDFromFullname(fullname):
	return re.findall('^(?:t\d_)?(.{4,8})', fullname)[0]


log.debug("Connecting to reddit")


# r = praw.Reddit(
# 	username=USERNAME
# 	,password=PASSWORD
# 	,client_id=CLIENT_ID
# 	,client_secret=CLIENT_SECRET
# 	,user_agent=USER_AGENT)
r = praw.Reddit(
	"Watchful1BotTest"
	,user_agent=USER_AGENT)


log.info(f"Logged into reddit as /u/{str(r.user.me())}")

while True:
	try:
		sub = r.subreddit(SUBREDDIT)
		for comment in sub.stream.comments(skip_existing=True):
			log.debug(f"Processing comment {comment.id} with parent {comment.parent_id}")
			body = comment.body.lower()
			if body.startswith("!lock") and sub.moderator(redditor=comment.author):
				addComment(getIDFromFullname(comment.parent_id))
				log.info(f"Added comment {comment.id}")

			elif body.startswith("!unlock") and sub.moderator(redditor=comment.author):
				removeComment(getIDFromFullname(comment.parent_id))
				log.info(f"Removed comment {comment.id}")

			elif isCommentLocked(getIDFromFullname(comment.parent_id)):
				log.info(f"Reply to locked comment {comment.parent_id}, removing {comment.id}")
				comment.mod.remove()

	except Exception as err:
		log.warning("Hit an error in main loop")
		log.warning(traceback.format_exc())

	time.sleep(LOOP_TIME)
