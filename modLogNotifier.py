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
from datetime import datetime
from datetime import timedelta

SUBREDDIT = "SubTestBot1"
USER_AGENT = "Mod Log Notifier (by /u/Watchful1)"
LOOP_TIME = 3 * 60
REDDIT_OWNER = "Watchful1"
DATABASE_NAME = "database.db"
LOG_LEVEL = logging.INFO
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


def signal_handler(signal, frame):
	log.info("Handling interupt")
	dbConn.commit()
	dbConn.close()
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


dbConn = sqlite3.connect(DATABASE_NAME)
c = dbConn.cursor()
c.execute('''
	CREATE TABLE IF NOT EXISTS logs (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		logID VARCHAR(80) NOT NULL,
		logCreated TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
		username VARCHAR(80) NOT NULL,
		UNIQUE (logID)
	)
''')
c.execute('''
	CREATE TABLE IF NOT EXISTS keystore (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		KeyName VARCHAR(80) NOT NULL,
		KeyValue VARCHAR(80) NOT NULL,
		UNIQUE (KeyName)
	)
''')
dbConn.commit()


def addLog(logId, username):
	c = dbConn.cursor()
	try:
		c.execute('''
			INSERT INTO logs
			(logID, username)
			VALUES (?, ?)
		''', (logId, username.lower()))
	except sqlite3.IntegrityError:
		return False

	dbConn.commit()
	return True


def getLogsOverLimit():
	c = dbConn.cursor()
	results = []
	for row in c.execute('''
		SELECT username
		FROM logs
		GROUP BY username
		HAVING count(*) >= ?
		''', (INFRACTIONS_LIMIT,)):
		results.append(row[0])

	return results


def clearLogsForUser(username):
	c = dbConn.cursor()
	c.execute('''
		DELETE FROM logs
		WHERE username = ?
	''', (username.lower(),))
	dbConn.commit()

	if c.rowcount >= 1:
		return True
	else:
		return False


def clearOldLogs():
	c = dbConn.cursor()
	c.execute('''
		DELETE FROM logs
		WHERE logCreated < ?
	''', ((datetime.utcnow() - timedelta(days=DAYS_OLD_TO_CLEAR)).strftime("%Y-%m-%d %H:%M:%S"),))
	dbConn.commit()

	return True


def setKey(key, value):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT KeyName
		FROM keystore
		WHERE KeyName = ?
	''', (key,))
	if result.fetchone():
		try:
			c.execute('''
				UPDATE keystore
				SET KeyValue = ?
				WHERE KeyName = ?
			''', (value, key))
		except sqlite3.IntegrityError:
			return False
	else:
		try:
			c.execute('''
				INSERT INTO keystore
				(KeyName, KeyValue)
				VALUES (?, ?)
			''', (key, value))
		except sqlite3.IntegrityError:
			return False

	dbConn.commit()
	return True


def getValue(key):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT KeyValue
		FROM keystore
		WHERE KeyName = ?
	''', (key,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return None
	else:
		return resultTuple[0]


def deleteKey(key):
	c = dbConn.cursor()
	c.execute('''
		DELETE FROM keystore
		WHERE KeyName = ?
	''', (key,))
	dbConn.commit()

	if c.rowcount == 1:
		return True
	else:
		return False


once = False
debug = False
user = None
if len(sys.argv) >= 2:
	user = sys.argv[1]
	for arg in sys.argv:
		if arg == 'once':
			once = True
		elif arg == 'debug':
			debug = True
			log.setLevel(logging.DEBUG)
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

while True:
	try:
		startTime = time.perf_counter()
		log.debug("Starting run")

		parsedTo = getValue("parsed_to")
		if parsedTo is None:
			parsedTo = datetime.utcnow()
			setKey("parsed_to", parsedTo.strftime("%Y-%m-%d %H:%M:%S"))
		else:
			parsedTo = datetime.strptime(parsedTo, "%Y-%m-%d %H:%M:%S")

		newParsedTo = None
		for modLog in r.subreddit(SUBREDDIT).mod.log(limit=None):
			logDatetime = datetime.utcfromtimestamp(modLog.created_utc)
			if logDatetime < parsedTo:
				break
			if newParsedTo is None:
				newParsedTo = logDatetime + timedelta(seconds=1)
			log.debug(f"Parsing modlog: {modLog.id}")
			if modLog.action == 'removecomment' and modLog.details.lower() == REMOVAL_REASON.lower():
				log.info(f"Found matching removal, comment by {modLog.target_author}")
				addLog(modLog.id, modLog.target_author)

		if newParsedTo is not None:
			setKey("parsed_to", newParsedTo.strftime("%Y-%m-%d %H:%M:%S"))

		for username in getLogsOverLimit():
			log.info(f"User {username} over limit, sending message")
			r.subreddit(SUBREDDIT).message(f"User hit {REMOVAL_REASON} limit",
			                               f"User /u/{username} has hit {INFRACTIONS_LIMIT} removals in the "
			                               f"last {DAYS_OLD_TO_CLEAR} days")
			clearLogsForUser(username)

		clearOldLogs()

		log.debug("Run complete after: %d", int(time.perf_counter() - startTime))
	except Exception as err:
		log.warning("Hit an error in main loop")
		log.warning(traceback.format_exc())

	if once:
		break

	time.sleep(LOOP_TIME)