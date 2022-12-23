import requests
from collections import defaultdict
from datetime import datetime, timedelta
import time
import os
import json

subreddits = ['Calgary','Metal','MetalMemes','metaljerk','Metalcore','metalmusicians','BlackMetal','numetal','progmetal','metal_me_irl','doommetal','metalguitar','PowerMetal','Metal101']
ignored_users = ['[deleted]', 'automoderator']
lookback_days = 180
min_comments_per_sub = 1
file_name = "users.txt"
require_first_subreddit = True  # if true, print users that occur in the first subreddit and any one of the following ones. Otherwise just find the most overlap between all subs

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&order=desc&subreddit={}&before="

startTime = datetime.utcnow()#datetime.strptime("22-02-25 00:00:00", '%y-%m-%d %H:%M:%S')#
startEpoch = int(startTime.timestamp())
endTime = startTime - timedelta(days=lookback_days)
endEpoch = int(endTime.timestamp())
totalSeconds = startEpoch - endEpoch


if not os.path.exists("overlap_subreddits"):
	os.makedirs("overlap_subreddits")


def loadSubredditCommenters(subreddit):
	for filename in os.listdir("overlap_subreddits"):
		if filename.endswith(".txt") and filename.startswith(subreddit):
			count_comments = 0
			with open(os.path.join("overlap_subreddits", filename), 'r') as inputFile:
				commenters = defaultdict(int)
				for line in inputFile:
					items = line.split("	")
					if len(items) != 2:
						print(f"Error loading line for {subreddit}: {line}")
						continue
					user_comments = int(items[1])
					commenters[items[0]] = user_comments
					count_comments += user_comments

			dateString = filename.split("_")[-1][:-4]
			print(f"Loaded {len(commenters)} commenters for subreddit r/{subreddit} through {dateString}")
			dateThrough = datetime.strptime(dateString, '%Y-%m-%d')
			return commenters, int(dateThrough.timestamp()), count_comments

	return None, None, 0


def saveSubredditCommenters(subreddit, commenters, dateThrough):
	if dateThrough is None:
		return
	#print(f"Saving {len(commenters)} commenters for subreddit r/{subreddit} through {dateThrough.strftime('%Y-%m-%d')}")
	for filename in os.listdir("overlap_subreddits"):
		if filename.endswith(".txt") and filename.startswith(subreddit):
			os.remove(os.path.join("overlap_subreddits", filename))

	with open(os.path.join("overlap_subreddits", f"{subreddit}_{dateThrough.strftime('%Y-%m-%d')}.txt"), 'w') as outputFile:
		for commenter, countComments in commenters.items():
			outputFile.write(commenter)
			outputFile.write("	")
			outputFile.write(str(countComments))
			outputFile.write("\n")


def countCommenters(subreddit):
	commenters, previousEpoch, count = loadSubredditCommenters(subreddit)
	if previousEpoch < endEpoch:
		print(f"Full subreddit loaded: {subreddit}")
		return commenters
	if commenters is None:
		commenters = defaultdict(int)
		previousEpoch = startEpoch
	print(f"Counting commenters in: {subreddit}")
	breakOut = False
	currentDate = None
	while True:
		newUrl = url.format(subreddit)+str(previousEpoch)
		try:
			response = requests.get(newUrl, headers={'User-Agent': "Overlap counter by /u/Watchful1"})
		except (requests.exceptions.ReadTimeout, requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError):
			print(f"Pushshift timeout, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
			time.sleep(5)
			continue
		try:
			objects = response.json()['data']
		except json.decoder.JSONDecodeError:
			print(f"Decoding error, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
			time.sleep(5)
			continue

		time.sleep(1)  # pushshift is ratelimited. If we go too fast we'll get errors

		if len(objects) == 0:
			break
		for object in objects:
			previousEpoch = object['created_utc'] - 1
			if object['author'].lower() not in ignored_users:
				commenters[object['author']] += 1
			count += 1
			if count % 1000 == 0:
				currentDatetime = datetime.fromtimestamp(previousEpoch)
				print("r/{0} comments: {1}, {2}, {3:.2f}%".format(
					subreddit,
					count,
					currentDatetime.strftime("%Y-%m-%d"),
					((startEpoch - previousEpoch) / totalSeconds) * 100))
				if currentDatetime.date() != currentDate:
					saveSubredditCommenters(subreddit, commenters, currentDatetime)
					currentDate = currentDatetime.date()
			if previousEpoch < endEpoch:
				breakOut = True
				currentDate = datetime.fromtimestamp(previousEpoch).date()
				break
		if breakOut:
			break
	saveSubredditCommenters(subreddit, commenters, currentDate)
	print(f"Comments: {count}, commenters: {len(commenters)}")
	return commenters


commenterSubreddits = defaultdict(int)
is_first = True
for subreddit in subreddits:
	commenters = countCommenters(subreddit)

	for commenter in commenters:
		if require_first_subreddit and not is_first and commenter not in commenterSubreddits:
			continue
		if commenters[commenter] >= min_comments_per_sub:
			commenterSubreddits[commenter] += 1
	is_first = False

if require_first_subreddit:
	count_found = 0
	with open(file_name, 'w') as txt:
		txt.write(f"Commenters in r/{subreddits[0]} and at least one of r/{(', '.join(subreddits))}\n")
		for commenter, countSubreddits in commenterSubreddits.items():
			if countSubreddits >= 2:
				count_found += 1
				txt.write(f"{commenter}\n")
	print(f"{count_found} commenters in r/{subreddits[0]} and at least one of r/{(', '.join(subreddits))}")

else:
	sharedCommenters = defaultdict(list)
	for commenter, countSubreddits in commenterSubreddits.items():
		if countSubreddits >= len(subreddits) - 2:
			sharedCommenters[countSubreddits].append(commenter)

	commentersAll = len(sharedCommenters[len(subreddits)])
	commentersMinusOne = len(sharedCommenters[len(subreddits) - 1])
	commentersMinusTwo = len(sharedCommenters[len(subreddits) - 2])

	print(f"{commentersAll} commenters in all subreddits, {commentersMinusOne} in all but one, {commentersMinusTwo} in all but 2. Writing output to {file_name}")

	with open(file_name, 'w') as txt:
		if commentersAll == 0:
			txt.write(f"No commenters in all subreddits\n")
		else:
			txt.write(f"{commentersAll} commenters in all subreddits\n")
			for user in sorted(sharedCommenters[len(subreddits)], key=str.lower):
				txt.write(f"{user}\n")
		txt.write("\n")

		if commentersAll < 10 and len(subreddits) > 2:
			if commentersMinusOne == 0:
				txt.write(f"No commenters in all but one subreddits\n")
			else:
				txt.write(f"{commentersMinusOne} commenters in all but one subreddits\n")
				for user in sorted(sharedCommenters[len(subreddits) - 1], key=str.lower):
					txt.write(f"{user}\n")
			txt.write("\n")

			if commentersMinusOne < 10:
				if commentersMinusTwo == 0:
					txt.write(f"No commenters in all but two subreddits\n")
				else:
					txt.write(f"{commentersMinusTwo} commenters in all but two subreddits\n")
					for user in sorted(sharedCommenters[len(subreddits) - 2], key=str.lower):
						txt.write(f"{user}\n")
				txt.write("\n")
