import praw
import discord_logging
import re
from collections import defaultdict

log = discord_logging.init_logging()

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1")
	subreddit = reddit.subreddit("CompetitiveOverwatch")

	users = {}
	with open('commenters.txt', 'r') as input_file:
		for line in input_file:
			username, count_comments = line.split("\t")
			users[username] = int(count_comments)
	log.info(f"Loaded {len(users)} users")

	flairs = defaultdict(int)
	count_users = 0
	for flair in subreddit.flair():
		count_users += 1
		if count_users % 1000 == 0:
			log.info(f"{count_users:,} users")
		if flair['flair_text'] is None:
			continue
		if flair['user'].name not in users:
			continue
		match = re.findall(r":[\w-]+:", flair['flair_text'])
		for mat in match:
			flairs[mat] += users[flair['user'].name]
	log.info(f"{count_users:,} users")

	for flair, count in reversed(sorted(flairs.items(), key=lambda item: item[1])):
		log.info(f"{flair}	{count}")
