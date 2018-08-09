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
USER_AGENT = "vote counter (by /u/Watchful1)"
LOOP_TIME = 5 * 60
REDDIT_OWNER = "Watchful1"
SUBREDDIT_LINK = "https://www.reddit.com/r/{}/comments/".format(SUBREDDIT)
DATABASE_NAME = "database.db"
BACKLOG_HOURS = 0
START_TIME = datetime.utcnow()

### Logging setup ###
LOG_LEVEL = logging.DEBUG
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
	log.info("Handling interupt")
	dbConn.commit()
	dbConn.close()
	sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)


dbConn = sqlite3.connect(DATABASE_NAME)
c = dbConn.cursor()
c.execute('''
	CREATE TABLE IF NOT EXISTS votes (
		ID INTEGER PRIMARY KEY AUTOINCREMENT,
		CommentID VARCHAR(10) NOT NULL,
		Voter VARCHAR(80) NOT NULL,
		VotedFor VARCHAR(80) NOT NULL,
		UNIQUE (CommentID, Voter)
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


def addVote(commentID, voter, votedFor):
	c = dbConn.cursor()
	try:
		c.execute('''
			INSERT INTO votes
			(CommentID, Voter, VotedFor)
			VALUES (?, ?, ?)
		''', (commentID, voter.lower(), votedFor.lower()))
	except sqlite3.IntegrityError:
		return False

	dbConn.commit()
	return True


def getVotes():
	c = dbConn.cursor()
	results = []
	for row in c.execute('''
		SELECT VotedFor, count(*) as VoteNum
		FROM votes
		GROUP BY VotedFor
		ORDER BY VoteNum desc
		'''):
		results.append({"user": row[0], "votes": row[1]})

	return results


def clearVotes():
	c = dbConn.cursor()
	c.execute('''
		DELETE FROM votes
	''')
	dbConn.commit()

	if c.rowcount > 0:
		return True
	else:
		return False


def isCommentProcessed(commentID):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT CommentID
		FROM votes
		WHERE CommentID = ?
	''', (commentID,))

	resultTuple = result.fetchone()

	if not resultTuple:
		return False
	else:
		return True


def hasAuthorVoted(voter):
	c = dbConn.cursor()
	result = c.execute('''
		SELECT CommentID
		FROM votes
		WHERE Voter = ?
	''', (voter.lower(),))

	resultTuple = result.fetchone()

	if not resultTuple:
		return False
	else:
		return True


def addKey(key, value):
	c = dbConn.cursor()
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


def getIDFromFullname(fullname):
	return re.findall('^(?:t\d_)?(.{4,8})', fullname)[0]


log.debug("Connecting to reddit")

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


def redditorExists(username):
	try:
		id = r.redditor(username).id
		return True
	except Exception as err:
		return False


log.info("Logged into reddit as /u/{}".format(str(r.user.me())))

while True:
	try:
		for comment in r.subreddit(SUBREDDIT).stream.comments():
			if comment is None or datetime.utcfromtimestamp(comment.created_utc) < START_TIME - timedelta(hours=BACKLOG_HOURS) \
					or comment.author == r.user.me():
				continue
			log.info("Processing comment {} from /u/{}".format(comment.id, comment.author.name))
			voteThread = getValue("thread")
			body = comment.body.lower()
			if body.startswith("summonvotebot") and comment.author.name.lower() == REDDIT_OWNER.lower():
				log.info("Owner summoning vote bot")
				if voteThread is None:
					log.info("Successfully summoned for thread: {}".format(getIDFromFullname(comment.link_id)))
					addKey("thread", getIDFromFullname(comment.link_id))
					comment.reply("Thread activated")
				else:
					log.info("Bot already active in another thread")
					comment.reply("Bot is already activated in [this thread]({}{}). You need to close it there first."
					              .format(SUBREDDIT_LINK, voteThread))

			elif body.startswith("endvotebot") and comment.author.name.lower() == REDDIT_OWNER.lower():
				log.info("Owner ending vote bot")
				if voteThread is not None:
					log.info("Closing thread: {}".format(getIDFromFullname(comment.link_id)))
					votes = getVotes()
					bldr = ["Voting finished!\n\n"]
					for vote in votes:
						bldr.append(vote["user"])
						bldr.append(" has ")
						bldr.append(str(vote["votes"]))
						bldr.append(" vote(s)  \n")
					bldr.append("\n\n")
					bldr.append(votes[0]["user"])
					bldr.append(" wins!")
					r.submission(id=voteThread).reply(''.join(bldr))

					dbConn.commit()
					dbConn.close()

					copyfile(DATABASE_NAME,
					         voteThread + "-backup.db")

					dbConn = sqlite3.connect("database.db")

					clearVotes()
					deleteKey("thread")
				else:
					log.info("Bot not active in this thread")
					comment.reply("Bot is activated in [this thread]({}{})."
					              .format(SUBREDDIT_LINK, voteThread))

			elif voteThread is not None:
				if voteThread == getIDFromFullname(comment.link_id):
					log.info("Comment is in the active thread")
					if body.startswith("vote"):
						log.info("Vote comment")
						if isCommentProcessed(comment.id):
							log.info("Comment already processed")
						elif hasAuthorVoted(comment.author.name):
							log.info("Comment author has already voted")
						else:
							votedForArray = re.findall('(?:vote )(?:/u/)?(\w+)', body)
							if not len(votedForArray):
								log.info("Could not find a vote in comment")
							else:
								votedFor = votedForArray[0].lower()
								log.info("Found a vote: {}".format(votedFor))

								if not redditorExists(votedFor):
									log.info("Redditor doesn't exist")
								else:
									result = addVote(comment.id, comment.author.name, votedFor)
									if not result:
										log.info("Something went wrong")
									else:
										log.info("Successfully voted, posting comment")
										votes = getVotes()
										bldr = ["Vote tabulated!\n\n"]
										for vote in votes:
											bldr.append(vote["user"])
											bldr.append(" has ")
											bldr.append(str(vote["votes"]))
											bldr.append(" vote(s)  \n")
										comment.reply(''.join(bldr))

					else:
						log.info("Not a vote comment")

				else:
					log.info("Not in vote thread")
	except Exception as err:
		log.warning("Hit an error in main loop")
		log.warning(traceback.format_exc())

	if once:
		break

	time.sleep(LOOP_TIME)
