import json

import discord_logging
from datetime import datetime
import os
import re
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
	all_users = defaultdict(int)

	# skip_groups = [
	# 	re.compile(r"Subscription added, u/([\w\-_]+), r/([\w\-_]+), \w+"),
	# 	re.compile(r"Queuing \d+ for u/([\w\-_]+) in r/([\w\-_]+) : \w+"),
	# 	re.compile(r"Posting prompt for u/[\w\-_]+ in r/[\w\-_]+ : \w+"),
	# 	re.compile(r"User doesn't exist: u/[\w\-_]+"),
	# 	re.compile(r"u/[\w\-_]+ already (subscribed|updated) to u/[\w\-_]+ in r/[\w\-_]+"),
	# 	re.compile(r"Removed subscription for u/[\w\-_]+ to u/[\w\-_]+ in r/[\w\-_]+"),
	# 	re.compile(r"u/[\w\-_]+ changed from (update|subscription) to (update|subscription) for u/[\w\-_]+ in r/[\w\-_]+"),
	# 	re.compile(r"Purged u/[\w\-_]+: \d+ \| \d+ \| \d+"),
	# 	re.compile(r"Listing subscriptions for u/[\w\-_]+"),
	# 	re.compile(r"Could not find subscription for u/[\w\-_]+ to u/[\w\-_]+ in r/[\w\-_]+ to remove"),
	# 	re.compile(r"u/[\w\-_]+ doesn't have any subscriptions to list"),
	# 	re.compile(r"received 500 HTTP response"),
	# 	re.compile(r"Subject: UpdateMeBot Here! Post by u/[\w\-_]+ in r/[\w\-_]+"),
	# 	re.compile(r"^u/[\w\-_]+ has posted a new thread in r/[\w\-_]+$"),
	# 	re.compile(r"u/[\w\-_]+ doesn't exist when creating subscription"),
	# 	re.compile(r"Logged into reddit as u/UpdateMeBot"),
	# 	re.compile(r"Server error sending message. Sleeping in case it's transient"),
	# 	re.compile(r"Next time u/[\w\-_]+ posts in r/[\w\-_]+"),
	# 	re.compile(r"Could not find author u/[\w\-_]+ for removal"),
	# 	re.compile(r"u/[\w\-_]+ doesn't have any subscriptions to remove"),
	# 	re.compile(r"Removed update for u/[\w\-_]+ to u/[\w\-_]+ in r/[\w\-_]+"),
	# 	re.compile(r"Purging user u/[\w\-_]+"),
	# 	re.compile(r"Removed all \d+ subscriptions for u/[\w\-_]+"),
	# 	re.compile(r"Trigger in comment doesn't match regex result"),
	# 	re.compile(r"Message u/\[deleted] : [\w]+"),
	# 	re.compile(r"u_mybrotherareyou/"),
	# 	re.compile(r"1luucru/"),
	# 	re.compile(r"1lv7qsu/"),
	# 	re.compile(r"1lo6swu/"),
	# 	re.compile(r"1ls0ktu/"),
	# 	re.compile(r"1ijjsiu/"),
	# 	re.compile(r"1lujp7u/"),
	# 	re.compile(r"1jeci3u/"),
	# 	re.compile(r"1lwcvnc/"),
	# 	re.compile(r"1lg3ruu/"),
	# ]
	# match_groups = [
	# 	re.compile(r"Processing comment \w+ from u/([\w\-_]+)"),
	# 	re.compile(r"Message u/([\w\-_]+) : \w+"),
	# 	re.compile(r"Notifying u/([\w\-_]+) for u/[\w\-_]+ in r/[\w\-_]+ : \w+"),
	# 	re.compile(r"Failure sending notification message to u/([\w\-_]+)"),
	# 	re.compile(r"User blocked notification message: u/([\w\-_]+)"),
	# ]

	skip_groups = [
		re.compile(r"User doesn't exist: u/[\w\-_]+"),
		re.compile(r"User blocked notification message: u/[\w\-_]+"),
		re.compile(r"u/[\w\-_]+ timezone updated to"),
		re.compile(r"u/[\w\-_]+ clock type updated to"),
		re.compile(r"User u/[\w\-_]+ hit their recurring limit, deleting reminder \d+"),
		re.compile(r"Error processing message: \w+ : u/[\w\-_]+: ServerError : received 500 HTTP response"),
		re.compile(r"Message \w+ from u/AutoModerator is blacklisted, skipping"),
		re.compile(r"Could not parse date: .+, defaulting to one day"),
		re.compile(r"Could not parse date: .+, defaulting not allowed"),
		re.compile(r"Logged into reddit as u/RemindMeBot"),
		re.compile(r"Message \w+ from u/\[deleted] is blacklisted, skipping"),
		re.compile(r"Error processing message: \w+ : u/[\w\-_]+: \w+Error"),
	]
	match_groups = [
	 	re.compile(r"Processing comment \w+ from u/([\w\-_]+)"),
		re.compile(r"Message u/([\w\-_]+) : \w+"),
		re.compile(r"Sending reminder to u/([\w\-_]+) : \d+"),
	]

	log_folder = r"\\MYCLOUDPR4100\Public\logs\remindmebot"

	missed_lines = 0
	for log_file in os.listdir(log_folder):
		log.info(f"Processing {log_file}")

		# line = ""
		# lines_read = 0
		# try:
		# 	for line in open(os.path.join(log_folder, log_file), "r", encoding="utf-8"):
		# 		lines_read += 1
		# 		pass
		# except UnicodeDecodeError:
		# 	log.info(line)
		# 	log.info(str(lines_read))

		lines = open(os.path.join(log_folder, log_file), "r", encoding="utf-8").readlines()

		i = 0
		while True:
			if i >= len(lines):
				break
			line = lines[i].strip()
			i += 1
			if "u/" not in line:
				continue

			found = False
			for reg in match_groups:
				matches = reg.search(line)
				if matches:
					all_users[matches.group(1)] += 1
					found = True
					break
			if found:
				continue

			found = False
			for reg in skip_groups:
				if reg.search(line):
					found = True
					break
			if found:
				continue

			log.info(f"Missed line: {line}")
			if missed_lines > 10:
				log.info(f"Found users: {len(all_users)}")
				log.info(f"Processed lines: {i}/{len(lines)}")
				sys.exit()
			missed_lines += 1
		log.info(f"Processed lines {log_file}: {i}/{len(lines)}")

	log.info(f"Complete")
	log.info(f"Found users: {len(all_users)}")
	found_users = defaultdict(int)
	target_count = 2
	for i in range(1, 5):
		found_users_inner = defaultdict(int)
		for user, count in all_users.items():
			if count >= i:
				found_users_inner[user] += count
		log.info(f"Found users at or over {i}: {len(found_users_inner)}")
		if i == target_count:
			found_users = found_users_inner

	log.info(f"Using users: {len(found_users)}")
	existing_users = load_users()
	log.info(f"Existing users: {len(existing_users)}")

	for user in existing_users:
		found_users[user["name"]] += 1

	users = []
	for user, count in found_users.items():
		users.append({"name": user, "count": count, "sent": False, "failed": False})
	log.info(f"Added users at or over {target_count}: {len(users)}")

	save_users(users)
