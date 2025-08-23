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
	# file_handle.write(json.dumps(users, indent=4))
	# file_handle.close()
	# os.remove("remindmebot.txt")
	# os.rename("remindmebot_2.txt", "remindmebot.txt")


def load_users():
	file_handle = open("remindmebot.txt", "r", encoding="utf-8")
	users = json.load(file_handle)
	file_handle.close()
	return users


class Moderator:
	def __init__(self, username):
		self.name = username
		self.subreddits = []

	def count_over_million(self):
		count = 0
		for subreddit in self.subreddits:
			if subreddit.over_million():
				count += 1
		return count

	def count_over_hundredk(self):
		count = 0
		for subreddit in self.subreddits:
			if subreddit.over_hundredk():
				count += 1
		return count

	def count_unknown(self):
		count = 0
		for subreddit in self.subreddits:
			if subreddit.view_count == -1:
				count += 1
		return count

	def is_affected(self):
		return self.count_over_million() > 1 or self.count_over_hundredk() > 5

	def count_drop_million(self):
		return max(self.count_over_million() - 1, 0)

	def count_drop_hundredk(self):
		return max(self.count_over_hundredk() - 5, 0)


class Subreddit:
	def __init__(self, subreddit_name, view_count):
		self.name = subreddit_name
		self.view_count = view_count
		self.subscribers = -1
		self.moderators = []

	def over_million(self):
		return self.view_count > 1000000

	def over_hundredk(self):
		return self.view_count > 100000


if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1", user_agent="Mod limits checker")

	bots = {
		"admin-tattler",
		"AutoModerator",
		"comment-nuke",
		"toolboxnotesxfer",
		"FortniteStatusBot",
		"BattleBusBot",
		"MAGIC_EYE_BOT",
		"CustomModBot",
		"floodassistant",
		"SnooSync",
		"community-home",
		"live-quests",
		"subreddit-status",
		"FortniteRedditMods",
		"HomebaseBot",
		"WorldNewsMods",
		"auto-modmail",
		"purge-user",
		"hive-protect",
		"evasion-guard",
		"report-dismisser",
		"un-filter",
		"bot-bouncer",
		"IAmAModBot",
		"AssistantBOT1",
		"IAmAModBot",
		"spam-nuke",
		"modmail-userinfo",
		"spam-src-spotter",
		"LegoAdminBot",
		"drawing-app",
		"IAmAModBot",
		"automod-sync",
		"modmailtodiscord",
		"trendingtattler",
		"RepostSleuthBot",
		"FoodVisibilityBot",
		"modmailassistant",
		"ban-context",
		"image-sourcery",
		"DuplicateDestroyer",
		"comment-cap",
		"community-hub",
		"flairassistant",
		"flair-schedule",
		"ignoreassistant",
		"mod-mentions",
		"modqueue-enhance",
		"modqueue-tools",
		"onedayflair",
		"priority-reports",
		"reputatorbot",
		"self-ban",
		"sendtoany",
		"spambotbuster",
		"spotlight-app",
		"subchart",
		"sub-stats-bot",
		"urlcopy",
		"user-flair-bot",
		"spot-comments",
		"submission2wiki",
		"unscramble-game",
		"link-navi",
		"vip-bot",
		"modqueue-nuke",
		"modmailremindme",
		"app-reply-notify",
		"timed-highlights",
		"image-moderator",
		"queue-pruner",
		"BotDefense",
		"MaxImageBot",
		"ModeratelyHelpfulBot",
		"ContextModBot",
		"Portrait_Robot",
		"Piercing-Moderator",
		"auto-post-lock",
		"automod-toggle",
	}

	subreddit_string = """
worldnews	4,404,769
lego	1,192,877
FortNiteBR	811,376
bayarea	806,318
IAmA	755,361
food	509,222
florida	425,751
painting	270,030
drawing	211,425
orlando	210,722
ListOfSubreddits	198,192
legostarwars	196,810
PixelArt	167,262
learntodraw	141,263
pasta	109,622
1980s	103,412
Fortnite	101,693
ukraine	341,604
piercing	1,030,577
PeterExplainsTheJoke	7,099,944
AMA	2,125,246
dinosaurs	380,777
iamatotalpieceofshit	363,687
rocketleague	317,096
NoahGetTheBoat	292,572
metalworking	150,580
ITookAPicture	149,443
popculturechat	7,459,372
PublicFreakout	2,882,628
WhitePeopleTwitter	970,177
LosAngeles	610,920
NewOrleans	161,598
"""

	subreddits = {}
	for line in subreddit_string.split("\n"):
		if line == "":
			continue
		subreddit_name, view_count_string = line.split("\t")
		view_count = int(view_count_string.replace(",",""))
		subreddit = Subreddit(subreddit_name, view_count)
		subreddits[subreddit_name] = subreddit
	moderators = {}

	# subreddits = [
	# 	["bayarea", 806318],
	# 	["listofsubreddits", 198192],
	# ]

	for subreddit in list(subreddits.values()):
		for reddit_moderator in reddit.subreddit(subreddit.name).moderator():
			if reddit_moderator.name in bots:
				continue
			moderator = moderators.get(reddit_moderator.name, Moderator(reddit_moderator.name))

			subreddit.moderators.append(moderator)
			log.info(f"r/{subreddit.name}: {moderator.name}")
			if len(moderator.subreddits) == 0:
				for reddit_moderated_subreddit in reddit_moderator.moderated():
					if reddit_moderated_subreddit.subscribers < 10000:
						continue
					moderated_subreddit = subreddits.get(reddit_moderated_subreddit.display_name)
					if moderated_subreddit is None:
						moderated_subreddit = Subreddit(reddit_moderated_subreddit.display_name, -1)
						subreddits[moderated_subreddit] = moderated_subreddit
					if moderated_subreddit.subscribers == -1:
						moderated_subreddit.subscribers = reddit_moderated_subreddit.subscribers
					moderator.subreddits.append(moderated_subreddit)
			log.info(f"    {len(moderator.subreddits)}")
			# for moderated_subreddit in moderator.subreddits:
			# 	log.info(f"    {moderated_subreddit}")

	log.info(f"----------------------------------------------")

	unknown_subreddits = {}
	for subreddit in sorted(subreddits.values(), key=lambda x: x.view_count, reverse=True):
		log.info(f"r/{subreddit.name}")
		if subreddit.view_count == -1 and subreddit.name not in unknown_subreddits:
			unknown_subreddits[subreddit.name] = subreddit
		count_affected = 0
		for moderator in subreddit.moderators:
			if subreddit.over_million() and moderator.count_drop_million() > 0:
				count_affected += 1
			elif subreddit.over_hundredk() and moderator.count_drop_hundredk() > 0:
				count_affected += 1
			log.info(f"    u/{moderator.name}: {len(moderator.subreddits)} : {moderator.count_over_million()} : {moderator.count_over_hundredk()} : {moderator.count_unknown()}")
		log.info(f"        {count_affected}")

	log.info(f"----------------------------------------------")

	for subreddit in sorted(subreddits.values(), key=lambda x: x.view_count, reverse=True):
		if subreddit.view_count == -1:
			continue
		count_affected = 0
		count_unknown = 0
		for moderator in subreddit.moderators:
			if subreddit.over_million() and moderator.count_drop_million() > 0:
				count_affected += 1
			elif subreddit.over_hundredk() and moderator.count_drop_hundredk() > 0:
				count_affected += 1
			if moderator.count_unknown() > 0:
				count_unknown += 1
		print(f"{subreddit.name}	{subreddit.view_count}	{len(subreddit.moderators)}	{count_affected}	{count_unknown}")

	log.info(f"----------------------------------------------")
	log.info(f"Unknown subreddits")

	for subreddit in sorted(unknown_subreddits.values(), key=lambda x: x.subscribers, reverse=True):
		log.info(f"{subreddit.name}: {subreddit.subscribers}")


