#!/usr/bin/python3

import os
import logging.handlers
import requests
import traceback
import collections
import configparser
import praw
import sys
import time
from datetime import datetime

### Config
SUBREDDIT = "teenagers"
USERNAME = "Watchful1BotTest"
USER_AGENT = "Counter script (by /u/Watchful1)"
BEGIN = "2017-12-20"
END = "2018-01-01"
SUBMISSIONS_COMMENTS = "submission" # use "submission" or "comment"
OUTPUT = "users.txt"

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

# turn the string begin and end dates into epoch timestamps
beginEpoch = int(datetime.strptime(BEGIN, "%Y-%m-%d").timestamp())
endEpoch = int(datetime.strptime(END, "%Y-%m-%d").timestamp())

# our pushshift url with our submissions or comments endpoint and the subreddit
url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&subreddit={}&before=".format(SUBMISSIONS_COMMENTS, SUBREDDIT)

# let's use a dictionary of username to flair, we'll split it out when we do the username lookups. For now we just need
# to preserve the list of unique usernames and each ones associated flair
authors = {}

# a count of objects processed just for logging purposes
count = 0

# an epoch timestamp that we update with each iteration to get the next batch. We're iterating from newest to oldest,
# so go with the endEpoch
previousTime = endEpoch

log.debug("Searching {} from {} to {} in /r/{}".format(SUBMISSIONS_COMMENTS, BEGIN, END, SUBREDDIT))

# we've hit out exit condition and we want to break out of the main loop
breakOut = False

# iterate through all submissions/comments and build a dictionary of authors/flairs
startTime = time.perf_counter()
while True:
	newUrl = url+str(previousTime)
	json = requests.get(newUrl, headers={'User-Agent': USER_AGENT})
	objects = json.json()['data']
	if len(objects) == 0:
		break

	for object in objects:
		# if the author isn't in our dictionary, put it there with the flair
		if object['author'] not in authors:
			authors[object['author']] = object['author_flair_text']

		# update the timestamp with the current object's time so when we grab the next batch we know the start time
		previousTime = object['created_utc'] - 1
		count += 1

		# this object is before our begin, so let's break out of the loop
		if previousTime < beginEpoch:
			breakOut = True
			break

		# log out every 1000 objects, just so the user knows we're still running
		if count % 1000 == 0:
			log.info("Found {} users in {} posts so far: {}".format(len(authors), count, datetime.fromtimestamp(previousTime).strftime("%Y-%m-%d")))
	if breakOut:
		break

log.info("Found a total of {} users in {} objects in {} seconds".format(len(authors), count, int(time.perf_counter() - startTime)))

# now we need to look up the user creation times. First we log into reddit.
# There are a number of ways to do this. I like to use a praw.ini config file with all my accounts and just pass
# in the username. You could instead pass in the username, password, token and secret right in the arguments here.
# See https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html
# and https://praw.readthedocs.io/en/latest/tutorials/refresh_token.html
try:
	reddit = praw.Reddit(
		USERNAME
		,user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error("User "+USERNAME+" not in praw.ini, aborting")
	sys.exit(0)

# this is a neat little trick. It's a dictionary, just like {}, but if you access a value that doesn't exist,
# it's automatically set to the argument you pass in, in this case an empty set
users = collections.defaultdict(set)

log.info("Looking up creation dates for {} users".format(len(authors)))
startTime = time.perf_counter()
count = 0
for author in authors:
	try:
		userCreationDate = reddit.redditor(author).created_utc
	except Exception as e:
		continue

	if userCreationDate >= beginEpoch:
		# in our dictionary, go to the key of the flair and add the author
		users[authors[author]].add(author)

	count += 1
	if count % 50 == 0:
		seconds = int(time.perf_counter() - startTime)
		log.info("Looked up {} users out of {} in {} seconds. {} seconds per user. About {} seconds left".format(count, len(authors), seconds, round(seconds / count, 2), round((seconds / count) * (len(authors) - count), 0)))

log.info("Completed in {} seconds".format(int(time.perf_counter() - startTime)))

# now let's print them all out to our file

log.info("Printing users to {}".format(OUTPUT))

outFile = open(OUTPUT, 'w')
flairs = ['13', '14', '15', '16', '17', '18', '19', 'OLD']
for flair in flairs:
	log.info("{}: {}".format(flair, len(users[flair])))
	for user in users[flair]:
		outFile.write("{}: {}\n".format(flair, user))

outFile.close()
