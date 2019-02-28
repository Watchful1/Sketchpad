#!/usr/bin/python3

import praw
import os
import logging.handlers
import sys
import configparser
import signal
import time
import traceback

USER_AGENT = "Bulk flair updater (by /u/Watchful1)"
REDDIT_OWNER = "Watchful1"
LOG_LEVEL = logging.INFO

SUBREDDIT = "sports"
USERNAME = ""
PASSWORD = ""
CLIENT_ID = ""
CLIENT_SECRET = ""

# use this section to switch every flair of one css class to a new css class, leaving the text alone
# turn it on by changing the False on the next line to True
flair_css_mapping_enabled = False
flair_css_mapping = {
	'oldCss1': 'newCss1',
	'oldCss2': 'newCss2',
}

# use this section to change all flair with one text to a new text, leaving the text alone
# turn it on by changing the False on the next line to True
flair_text_mapping_enabled = False
flair_text_mapping = {
	'oldText1': 'newText1',
	'oldText2': 'newText2',
}

# use this section to change combinations of css class and text into a different css class and text
# if this is enabled and a users flair matches something here, it will override the settings above
# turn it on by changing the False on the next line to True
flair_css_text_mapping_enabled = False
flair_css_text_mapping = {
	'oldCss1': {
		'oldText1': {'css': 'newCss1', 'text': 'newText1'},
		'oldText2': {'css': 'newCss2', 'text': 'newText2'},
	},
	'oldCss3': {
		'oldText3': {'css': 'newCss3', 'text': 'newText3'},
		'oldText4': {'css': 'newCss4', 'text': 'newText4'},
	},
}

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


if (flair_css_mapping_enabled or flair_text_mapping_enabled) and flair_css_text_mapping_enabled:
	log.warning("Warning, you can't use the css_text section at the same time as the other two")
	sys.exit()


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

log.info("Logged into reddit as /u/{}".format(str(r.user.me())))

try:
	sub = r.subreddit(SUBREDDIT)
	startTime = time.perf_counter()

	numFlairs = 0
	flair_map = []
	for flair in sub.flair(limit=None):
		numFlairs += 1

		item = {
			'user': flair['user'].name,
			'flair_text': flair['flair_text'],
			'flair_css_class': flair['flair_css_class'],
		}
		updated = False
		if flair_text_mapping_enabled:
			if flair['flair_text'] in flair_text_mapping:
				item['flair_text'] = flair_text_mapping[flair['flair_text']]
				updated = True

		if flair_css_mapping_enabled:
			if flair['flair_css_class'] in flair_text_mapping:
				item['flair_css_class'] = flair_text_mapping[flair['flair_css_class']]
				updated = True

		if flair_css_text_mapping_enabled:
			if flair['flair_css_class'] in flair_css_text_mapping and \
					flair['flair_text'] in flair_css_text_mapping[flair['flair_css_class']]:
				result = flair_css_text_mapping[flair['flair_css_class']][flair['flair_text']]
				item['flair_css_class'] = result['css']
				item['flair_text'] = result['text']
				updated = True

		if updated:
			log.info("/u/%s from '%s|%s' to '%s|%s'",
					 flair['user'].name,
					 flair['flair_css_class'],
					 flair['flair_text'],
					 item['flair_css_class'],
					 item['flair_text'])
			flair_map.append(item)
		else:
			log.debug("/u/%s unchanged from '%s|%s'", flair['user'].name, flair['flair_css_class'], flair['flair_text'])

	log.info("Found %d flairs in %d seconds", numFlairs, int(time.perf_counter() - startTime))
	startTime = time.perf_counter()
	log.info("Updating %d flairs. Running update function, this could take a while.", len(flair_map))
	sub.flair.update(flair_map)
	log.info("Done in %d seconds", int(time.perf_counter() - startTime))
except Exception as err:
	log.warning("Hit an error in main loop")
	log.warning(traceback.format_exc())
