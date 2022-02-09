import requests
from collections import defaultdict
from datetime import datetime, timedelta
import time
import re
import json
import os

subreddits = ['NFTgiveaway', 'NFTExchange', 'opensea', 'NFTsMarketplace']
lookback_days = 365

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&subreddit={}&before="

startTime = datetime.utcnow()
startEpoch = int(startTime.timestamp())
endTime = startTime - timedelta(days=lookback_days)
endEpoch = int(endTime.timestamp())
totalSeconds = startEpoch - endEpoch


def loadSubredditKeywords(subreddit):
	keywords = set()
	for filename in os.listdir("keyword_subreddits"):
		if filename.endswith(".txt") and filename.startswith(subreddit):
			with open(os.path.join("keyword_subreddits", filename), 'r') as inputFile:
				for line in inputFile:
					if line:
						keywords.add(line.strip())

			dateString = filename.split("_")[-1][:-4]
			print(f"Loaded {len(keywords)} keywords for subreddit r/{subreddit} through {dateString}")
			dateThrough = datetime.strptime(dateString, '%Y-%m-%d')
			return keywords, int(dateThrough.timestamp())

	return None, None


def saveSubredditCommenters(subreddit, keywords, dateThrough):
	if dateThrough is None:
		return
	for filename in os.listdir("keyword_subreddits"):
		if filename.endswith(".txt") and filename.startswith(subreddit):
			os.remove(os.path.join("keyword_subreddits", filename))

	with open(os.path.join("keyword_subreddits", f"{subreddit}_{dateThrough.strftime('%Y-%m-%d')}.txt"), 'w') as outputFile:
		for keyword in keywords:
			try:
				outputFile.write(keyword)
				outputFile.write("\n")
			except UnicodeEncodeError:
				continue


def searchKeywords(subreddit, regex):
	keywords, previousEpoch = loadSubredditKeywords(subreddit)
	if keywords is None:
		keywords = set()
		previousEpoch = startEpoch
	print(f"Searching comments in : {subreddit}")
	breakOut = False
	count = 0
	currentDate = None
	while True:
		newUrl = url.format(subreddit)+str(previousEpoch)
		try:
			response = requests.get(newUrl, headers={'User-Agent': "Overlap counter by /u/Watchful1"})
		except (requests.exceptions.ReadTimeout, requests.exceptions.ChunkedEncodingError):
			print(f"Pushshift timeout, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
			time.sleep(5)
			continue
		try:
			comments = response.json()['data']
		except json.decoder.JSONDecodeError:
			print(f"Decoding error, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
			time.sleep(5)
			continue

		time.sleep(0.2)  # pushshift is ratelimited. If we go too fast we'll get errors

		if len(comments) == 0:
			break
		for comment in comments:
			previousEpoch = comment['created_utc'] - 1

			result = regex.search(comment['body'])
			if result is not None:
				keyword = result.group(1)
				if len(keyword) == 42:
					keywords.add(keyword)

			count += 1
			if count % 1000 == 0:
				currentDatetime = datetime.fromtimestamp(previousEpoch)
				print("r/{0} comments: {1}, {2}, {3:.2f}%".format(
					subreddit,
					count,
					currentDatetime.strftime("%Y-%m-%d"),
					((startEpoch - previousEpoch) / totalSeconds) * 100))
				if currentDatetime.date() != currentDate:
					saveSubredditCommenters(subreddit, keywords, currentDatetime)
					currentDate = currentDatetime.date()
			if previousEpoch < endEpoch:
				breakOut = True
				currentDate = datetime.fromtimestamp(previousEpoch).date()
				break
		if breakOut:
			break
	print(f"Comments: {count}, keywords: {len(keywords)}")
	return keywords


if __name__ == "__main__":
	if not os.path.exists("keyword_subreddits"):
		os.makedirs("keyword_subreddits")

	all_keywords = set()
	regex = re.compile(r"(0x\w+)")
	for subreddit in subreddits:
		keywords = searchKeywords(subreddit, regex)
		print(f"Adding {len(keywords)} to {len(all_keywords)}")
		for keyword in keywords:
			all_keywords.add(keyword)
		print(f"Now have {len(all_keywords)}")

	with open("addresses.txt", 'w') as txt:
		for keyword in all_keywords:
			try:
				txt.write(keyword)
				txt.write("\n")
			except UnicodeEncodeError:
				continue
