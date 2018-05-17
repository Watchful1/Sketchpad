#!/usr/bin/python3

import os
import logging.handlers
import requests
import time
import traceback
import collections
import bisect
from datetime import datetime
from datetime import timedelta

### Config ###
SUBREDDIT = "office"
USER_AGENT = "Domain script (by /u/Watchful1)"
DAYS = 5
OUTPUT = "users.txt"

### Logging setup ###
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

targetTime = int((datetime.utcnow() - timedelta(days=DAYS)).timestamp())
log.debug("Going back {} days".format(DAYS))
url = "https://api.pushshift.io/reddit/submission/search?limit=1000&sort=desc&subreddit={}&before=".format(SUBREDDIT)
previousTime = int(time.mktime(datetime.utcnow().timetuple()))
count = 0
users = collections.defaultdict(lambda: collections.defaultdict(int))
log.info("Finding posts")
breakOut = False
while True:
	newUrl = url+str(previousTime)
	json = requests.get(newUrl, headers={'User-Agent': USER_AGENT})
	posts = json.json()['data']
	if len(posts) == 0:
		break

	for post in posts:
		if not post['is_self']:
			users[post['author']]["v.redd.it" if post['is_video'] else post['domain']] += 1

		previousTime = post['created_utc'] - 1
		count += 1
		if previousTime < targetTime:
			breakOut = True
			break

		if count % 500 == 0:
			log.info("Found {} posts so far".format(count))
	if breakOut:
		break

log.info("Found {} total posts".format(count))

log.info("Sorting users")
sortedUsers = []
for user in users:
	bisect.insort(sortedUsers, user)

log.info("Outputting users to: {}".format(OUTPUT))
outFile = open(OUTPUT, 'w')
for user in sortedUsers:
	userDomains = []
	for domain in users[user]:
		bisect.insort(userDomains, (users[user][domain], domain))

	for domainTuple in userDomains[::-1]:
		outFile.write("{}: {}, {}\n".format(user, domainTuple[1], domainTuple[0]))
	#log.debug("{}: {}".format(user, ', '.join(bldr)))
