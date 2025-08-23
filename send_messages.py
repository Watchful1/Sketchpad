import praw

import discord_logging
from datetime import datetime
import os
import json
from collections import defaultdict
import sys


log = discord_logging.init_logging()


def save_users(users):
	file_handle = open("remindmebot_2.txt", "w", encoding="utf-8")
	file_handle.write(json.dumps(users, indent=4))
	file_handle.close()
	os.remove("remindmebot.txt")
	os.rename("remindmebot_2.txt", "remindmebot.txt")


def load_users():
	file_handle = open("remindmebot.txt", "r", encoding="utf-8")
	users = json.load(file_handle)
	file_handle.close()
	return users


if __name__ == "__main__":
	subject = "UpdateMeBot will now send chats instead of DMs. How not to miss them, plus looking for feedback"
	body = """You're getting this message since you interacted with the bot multiple times in the last two months. If you aren't interested, just ignore it.

If you are a user of the bot and don't want to miss updates, start a chat with u/UpdateMeBot and send it "hello" so it can talk to you.

There's more details and I'm also looking for feedback on the post here: https://www.reddit.com/r/UpdateMeBot/comments/1mbnum8/updatemebot_will_now_send_chats_instead_of_dms/"""

	users = load_users()
	log.info(f"{len(users)}")

	reddit = praw.Reddit("UpdateMeBot", user_agent="Manual message sender")

	sent, success = 0, 0
	for user in users:
		if user["sent"]:
			log.info(f"{sent}/{len(users)}: Already sent to u/{(user['name'])}")
			sent += 1
			continue

		try:
			log.info(f"{sent}/{len(users)}: Sending to u/{(user['name'])}")
			reddit.redditor(user["name"]).message(subject=subject, message=body)
			success += 1
		except Exception as e:
			log.warning(f"Send failed to u/{(user['name'])} with {(user['count'])} : {e}")
			user["failed"] = True

		sent += 1
		user["sent"] = True
		save_users(users)
