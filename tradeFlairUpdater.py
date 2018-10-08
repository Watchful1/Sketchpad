#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import requests
import re
from datetime import datetime


SUBREDDIT = "comicswap"
USER_AGENT = "Trade flair updater (by /u/Watchful1)"
LOOP_TIME = 5 * 60
REDDIT_OWNER = "Watchful1"
LOG_LEVEL = logging.INFO
CONFIG_FILE = "config.ini"
TIME_FORMAT = "%m-%d-%Y %I:%M %p"
TIERS = [
	{'start': 1, 'text': "Single Issue"},
	{'start': 5, 'text': "Annual"},
	{'start': 10, 'text': "Trade Paperback"},
	{'start': 20, 'text': "Trusted"},
]

USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""


LOG_FOLDER_NAME = "logs"
if not os.path.exists(LOG_FOLDER_NAME):
	os.makedirs(LOG_FOLDER_NAME)
LOG_FILENAME = LOG_FOLDER_NAME + "/" + "bot.log"
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

log.info(f"Logged into reddit as /u/{str(r.user.me())}")


def incrementFlair(flair_text, user, sub):
	if flair_text == "None":
		trades = 1
	else:
		nums = re.findall('(\d+)', str(flair_text))
		if len(nums) != 1:
			log.info(f"Couldn't find number in flair, setting to 1: {flair_text}")
			trades = 1
		else:
			trades = int(nums[0])

	if trades >= 20:
		log.info("20+ trades, not updating flair")
	else:
		log.info(f"Setting trades to {trades} for /u/{user.name}")
		for tier in TIERS:
			if tier['start'] > trades:
				break
			text = tier['text']
		flair = f"{text}: {trades}{'+' if trades >= 20 else ''}"
		log.debug(f"Setting flair to {flair}")
		sub.flair.set(user, flair)


startTime = datetime.utcnow()

config = configparser.ConfigParser()
config.read(CONFIG_FILE)
if 'previous' not in config.sections():
	lastTime = startTime
	log.info(f"Config not found, setting start time to {lastTime.strftime(TIME_FORMAT)}")
	config['previous'] = {}
	config['previous']['datetime'] = datetime.strftime(lastTime, TIME_FORMAT)
	with open(CONFIG_FILE, 'w') as configfile:
		config.write(configfile)
else:
	strTime = config['previous']['datetime']
	log.info(f"Loading last run time as {strTime}")
	lastTime = datetime.strptime(strTime, TIME_FORMAT)

log.info(f"Running for {startTime - lastTime}")

url = f"https://api.pushshift.io/reddit/comment/search?q=confirmed&limit=1000&sort=desc&subreddit={SUBREDDIT}&before="
previousEpoch = int(startTime.timestamp())
lastEpoch = int(lastTime.timestamp())
breakOut = False

sub = r.subreddit(SUBREDDIT)
while True:
	newUrl = url+str(previousEpoch)
	log.debug(f"URL: {newUrl}")
	json = requests.get(newUrl, headers={'User-Agent': USER_AGENT})
	objects = json.json()['data']
	if len(objects) == 0:
		log.info("No objects in json, breaking")
		break

	for object in objects:
		previousEpoch = object['created_utc'] - 1
		if previousEpoch < lastEpoch:
			log.info("Hit an object older than the previous run time, run complete")
			breakOut = True
			break

		comment = r.comment(object['id'])
		parent = comment.parent()
		log.info(f"Found new confirmation from /u/{object['author']} for /u/{parent.author.name}, comment {comment.id}")
		incrementFlair(comment.author_flair_text, comment.author, sub)
		incrementFlair(parent.author_flair_text, parent.author, sub)
	if breakOut:
		break

config['previous']['datetime'] = datetime.strftime(startTime, TIME_FORMAT)
with open(CONFIG_FILE, 'w') as configfile:
	config.write(configfile)