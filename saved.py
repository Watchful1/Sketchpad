import discord_logging
import praw


log = discord_logging.init_logging()


def count_saved(r):
	i = 0
	for item in r.user.me().saved(limit=None):
		i += 1

	log.info(f"Saved: {i}")


def clear_saved(r):
	i = 0
	for item in r.user.me().saved(limit=None):
		item.unsave()
		i += 1

	log.info(f"Cleared: {i}")


def save_items(r, j):
	i = 0
	for comment in r.subreddit("askreddit").comments():
		comment.save()
		i += 1
		if i >= 100:
			break

	log.info(f"Saved new items: {i + j}")
	return i + j


r = praw.Reddit("Watchful1BotTest")

clear_saved(r)
count_saved(r)

j = 0
for i in range(5):
	j = save_items(r, j)

count_saved(r)
clear_saved(r)
clear_saved(r)
count_saved(r)

