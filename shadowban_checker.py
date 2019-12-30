#!/usr/bin/python3

import praw
import sys
import logging.handlers
import discord_logging
import configparser
import time

USER_AGENT = "Shadowban checker (by /u/Watchful1)"
LOOP_TIME = 10
LOG_LEVEL = logging.INFO

USERNAME = "RemindMeBot"

log = discord_logging.init_logging()

user = None
if len(sys.argv) >= 2:
	user = sys.argv[1]

if user is None:
	log.warning("User not provided")
	sys.exit()

discord_logging.init_discord_logging(user, logging.WARNING, 1)

try:
	r = praw.Reddit(
		user
		, user_agent=USER_AGENT)
except configparser.NoSectionError:
	log.error(f"User {user} not in praw.ini, aborting")
	sys.exit(0)

log.info("Logged into reddit as /u/{}".format(str(r.user.me())))

unban_published = False
while True:
	try:
		fullname = r.redditor(USERNAME).fullname

		if not unban_published:
			log.warning(f"<@95296130761371648> u/{USERNAME} is unbanned!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
			unban_published = True

		log.info(f"u/{USERNAME} is not banned")
	except Exception as err:
		log.info(f"u/{USERNAME} is banned")

	time.sleep(LOOP_TIME)
