import praw

import discord_logging
from datetime import datetime
import os
import json
from collections import defaultdict
import sys


log = discord_logging.init_logging()


def save_data(holder, clean=False):
	file_handle = open("subreddits_2.txt", "w", encoding="utf-8")
	count_subs, count_mods = 0,0
	for subreddit in holder.subreddits.values():
		moderator_names = subreddit.moderator_names()
		if clean and not len(moderator_names):
			continue
		file_handle.write(subreddit.name)
		file_handle.write(":")
		file_handle.write(str(subreddit.subscribers))
		file_handle.write(":")
		file_handle.write("1" if subreddit.complete else "0")
		file_handle.write(":")
		file_handle.write(','.join(moderator_names))
		file_handle.write("\n")
		count_subs += 1
	file_handle.write("----------\n")
	for moderator in holder.moderators.values():
		subreddit_names = moderator.subreddit_names()
		if clean and not len(subreddit_names):
			continue
		file_handle.write(moderator.name)
		file_handle.write(":")
		file_handle.write("1" if moderator.complete else "0")
		file_handle.write(":")
		file_handle.write(','.join(subreddit_names))
		file_handle.write("\n")
		count_mods += 1
	file_handle.close()
	if os.path.exists("subreddits.txt"):
		os.remove("subreddits.txt")
	os.rename("subreddits_2.txt", "subreddits.txt")
	log.info(f"Saved {count_subs} subreddits and {count_mods} moderators")


def load_data(bots, subreddits_string):
	holder = DataHolder(bots)
	if not os.path.exists("subreddits.txt"):
		return holder

	file_handle = open("subreddits.txt", "r", encoding="utf-8")
	reading_moderators = False
	for line in file_handle:
		if line.strip() == "":
			continue
		if line.strip() == "----------":
			reading_moderators = True
			continue
		if not reading_moderators:
			subreddit_name, subscribers, complete, moderators_line = line.strip().lower().split(":")
			subreddit = holder.get_or_add_subreddit(subreddit_name)
			subreddit.subscribers = int(subscribers)
			subreddit.complete = complete == "1"
			if moderators_line != "":
				for moderator_name in moderators_line.split(","):
					holder.get_or_add_moderator(moderator_name, subreddit_name)
		else:
			moderator_name, complete, subreddits_line = line.strip().lower().split(":")
			moderator = holder.get_or_add_moderator(moderator_name)
			if moderator is not None:
				moderator.complete = complete == "1"
				if subreddits_line != "":
					for subreddit_name in subreddits_line.split(","):
						holder.get_or_add_subreddit(subreddit_name, moderator_name)

	file_handle.close()

	for line in subreddit_string.split("\n"):
		if line == "":
			continue
		subreddit_name, view_count_string = line.lower().split("\t")
		view_count = int(view_count_string.replace(",", ""))
		subreddit = holder.get_or_add_subreddit(subreddit_name)
		subreddit.view_count = view_count

	return holder


class DataHolder:
	def __init__(self, bots):
		self.subreddits = {}
		self.moderators = {}
		self.bots = bots

	def get_or_add_subreddit(self, subreddit_name, moderator_name=None):
		subreddit_name = subreddit_name.lower()
		subreddit = self.subreddits.get(subreddit_name)
		if subreddit is None:
			subreddit = Subreddit(subreddit_name)
			self.subreddits[subreddit_name] = subreddit
		if moderator_name is not None:
			moderator_name = moderator_name.lower()
			if moderator_name not in self.bots:
				moderator = self.moderators.get(moderator_name)
				if moderator is None:
					moderator = Moderator(moderator_name)
					self.moderators[moderator_name] = moderator

				moderator.subreddits[subreddit_name] = subreddit
				subreddit.moderators[moderator.name] = moderator
		return subreddit

	def get_or_add_moderator(self, moderator_name, subreddit_name=None):
		moderator_name = moderator_name.lower()
		if moderator_name in self.bots:
			return None
		moderator = self.moderators.get(moderator_name)
		if moderator is None:
			moderator = Moderator(moderator_name)
			self.moderators[moderator_name] = moderator

		if subreddit_name is not None:
			subreddit_name = subreddit_name.lower()
			subreddit = self.subreddits.get(subreddit_name)
			if subreddit is None:
				subreddit = Subreddit(subreddit_name)
				self.subreddits[subreddit_name] = subreddit

			subreddit.moderators[moderator.name] = moderator
			moderator.subreddits[subreddit_name] = subreddit
		return moderator


class Moderator:
	def __init__(self, username, complete=False):
		self.name = username
		self.subreddits = {}
		self.complete = complete

	def __str__(self):
		return self.name

	def count_over_million(self):
		count = 0
		for subreddit in self.subreddits.values():
			if subreddit.over_million():
				count += 1
		return count

	def count_over_hundredk(self):
		count = 0
		for subreddit in self.subreddits.values():
			if subreddit.over_hundredk():
				count += 1
		return count

	def count_unknown(self):
		count = 0
		for subreddit in self.subreddits.values():
			if subreddit.view_count == -1:
				count += 1
		return count

	def is_affected(self):
		return self.count_over_million() > 1 or self.count_over_hundredk() > 5

	def count_drop_million(self):
		return max(self.count_over_million() - 1, 0)

	def count_drop_hundredk(self):
		return max(self.count_over_hundredk() - 5, 0)

	def subreddit_names(self):
		names = []
		for subreddit in self.subreddits.values():
			names.append(subreddit.name)
		return names


class Subreddit:
	def __init__(self, subreddit_name, view_count=-1, subscribers=-1, complete=False):
		self.name = subreddit_name
		self.view_count = view_count
		self.subscribers = subscribers
		self.moderators = {}
		self.complete = complete

	def __str__(self):
		return self.name

	def over_million(self):
		return self.view_count > 1000000

	def over_hundredk(self):
		return self.view_count > 100000

	def get_view_count(self):
		if self.view_count == -1:
			if self.subscribers == -1:
				return -1
			return self.subscribers
		return self.view_count

	def is_estimated(self):
		return self.view_count == -1

	def moderator_names(self):
		names = []
		for moderator in self.moderators.values():
			names.append(moderator.name)
		return names


if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1", user_agent="Mod limits checker")

	bots = set()
	with open("bots.txt", "r", encoding="utf-8") as file_handle:
		for line in file_handle:
			bots.add(line.strip().lower())

	log.info(f"Loaded {len(bots)} mod bots")

	subreddit_string = """
bayarea	806,318
ListOfSubreddits	198,192
FortNiteBR	811,376
Fortnite	101,693
worldnews	4,404,769
IAmA	755,361
florida	425,751
orlando	210,722
ukraine	341,604
lego	1,192,877
legostarwars	196,810
painting	270,030
drawing	211,425
PixelArt	167,262
learntodraw	141,263
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
help	600,156
EndTipping	245,827
WFH	205,961
vintage	61,556
fortyfivefiftyfive	173,618
PixelArt	167,262
Fallout76Marketplace	12,305
Windows11	828,778
WindowsHelp	823,120
Windows10	812,096
windows	527,176
MicrosoftTeams	209,715
tattoos	1,310,000
fightporn	876,302
outfits	798,890
vancouver	584,432
rocks	189,741
askvan	188,398
software	603,733
nationalpark	210,374
msp	163,538
medical	160,809
brasil	518,552
findareddit	172,572
NewToReddit	161,630
opiniaoimpopular	156,415
MemesBR	146,435
saopaulo	120,223
PergunteReddit	117,523
drugs	313,495
"""

	holder = load_data(bots, subreddit_string)

	# loop through subreddits to get the ones we need to look up
	subreddits_to_lookup = []
	for subreddit in holder.subreddits.values():
		if subreddit.view_count != -1 and not subreddit.complete:
			subreddits_to_lookup.append(subreddit)
	log.info(f"{len(subreddits_to_lookup)} subreddits to lookup moderator list")

	# loop though them and lookup the moderator list
	i = 0
	for subreddit in subreddits_to_lookup:
		i += 1
		for reddit_moderator in reddit.subreddit(subreddit.name).moderator():
			moderator = holder.get_or_add_moderator(reddit_moderator.name, subreddit.name)
		subreddit.complete = True
		log.info(f"{i}/{len(subreddits_to_lookup)}: r/{subreddit.name} has {len(subreddit.moderators)} moderators")

	save_data(holder)

	# loop through moderators to get list of ones to lookup
	moderators_to_lookup = []
	for moderator in holder.moderators.values():
		if not moderator.complete:
			moderators_to_lookup.append(moderator)

	# loop through moderators to get sub list
	i = 0
	for moderator in moderators_to_lookup:
		i += 1
		for reddit_subreddit in reddit.redditor(moderator.name).moderated():
			if reddit_subreddit.subscribers < 10000:
				continue
			subreddit = holder.get_or_add_subreddit(reddit_subreddit.display_name, moderator.name)
			if subreddit.subscribers == -1:
				subreddit.subscribers = reddit_subreddit.subscribers
		moderator = holder.get_or_add_moderator(moderator.name)
		moderator.complete = True
		log.info(f"{i}/{len(moderators_to_lookup)}: u/{moderator.name} has {len(moderator.subreddits)} subreddits")
		# if i >= 200:
		# 	break

	save_data(holder, clean=True)
	holder = load_data(bots, subreddit_string)


	# log.info(f"Top moderators")
	# sorted_moderators = []
	# for moderator in holder.moderators.values():
	# 	sorted_moderators.append((moderator.name, len(moderator.subreddits)))
	# sorted_moderators = sorted(sorted_moderators, key=lambda x: x[1], reverse=True)
	# for moderator_name, count in sorted_moderators[:10]:
	# 	log.info(f"u/{moderator_name} : {count}")

	unknown_subreddits = {}
	for subreddit in sorted(holder.subreddits.values(), key=lambda x: x.get_view_count(), reverse=True):
		log.info(f"r/{subreddit.name}")
		if subreddit.view_count == -1 and subreddit.name not in unknown_subreddits:
			unknown_subreddits[subreddit.name] = subreddit
		count_affected = 0
		for moderator in subreddit.moderators.values():
			if subreddit.over_million() and moderator.count_drop_million() > 0:
				count_affected += 1
			elif subreddit.over_hundredk() and moderator.count_drop_hundredk() > 0:
				count_affected += 1
			log.info(f"    u/{moderator.name}: {len(moderator.subreddits)} : {moderator.count_over_million()} : {moderator.count_over_hundredk()} : {moderator.count_unknown()}")
		log.info(f"        {count_affected}")

	log.info(f"----------------------------------------------")

	for subreddit in sorted(holder.subreddits.values(), key=lambda x: x.get_view_count(), reverse=True):
		if subreddit.view_count == -1:
			continue
		count_affected = 0
		count_unknown = 0
		for moderator in subreddit.moderators.values():
			if subreddit.over_million() and moderator.count_drop_million() > 0:
				count_affected += 1
			elif subreddit.over_hundredk() and moderator.count_drop_hundredk() > 0:
				count_affected += 1
			if moderator.count_unknown() > 0:
				count_unknown += 1
		print(f"{subreddit.name}	{subreddit.view_count}	{len(subreddit.moderators)}	{count_affected}	{count_unknown}")

	# log.info(f"----------------------------------------------")
	# log.info(f"Unknown subreddits")
	#
	# for subreddit in sorted(unknown_subreddits.values(), key=lambda x: x.subscribers, reverse=True):
	# 	log.info(f"{subreddit.name}: {subreddit.subscribers}")


