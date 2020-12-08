import requests
from collections import defaultdict
from datetime import datetime
from datetime import timedelta
import time
import json

subreddits = ['redditdev', 'requestabot', 'botwatch']
ignored_users = ['[deleted]', 'automoderator']
lookback_days = 180
min_comments_per_sub = 1
file_name = "users.txt"
# either author, comments or leave it empty
sort_by = ""

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&subreddit={}&before="

startTime = datetime.utcnow()
startEpoch = int(startTime.timestamp())
endTime = startTime - timedelta(days=lookback_days)
endEpoch = int(endTime.timestamp())
totalSeconds = startEpoch - endEpoch


def countCommenters(subreddit):
	count = 0
	commenters = defaultdict(int)
	previousEpoch = startEpoch
	print(f"Counting commenters in: {subreddit}")
	breakOut = False
	while True:
		newUrl = url.format(subreddit)+str(previousEpoch)
		try:
			response = requests.get(newUrl, headers={'User-Agent': "Overlap counter by /u/Watchful1"})
		except requests.exceptions.ReadTimeout:
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
			if object['author'] not in ignored_users:
				commenters[object['author']] += 1
			count += 1
			if count % 1000 == 0:
				print("r/{0} comments: {1}, {2}, {3:.2f}%".format(
					subreddit,
					count,
					datetime.fromtimestamp(previousEpoch).strftime("%Y-%m-%d"),
					((startEpoch - previousEpoch) / totalSeconds) * 100))
			if previousEpoch < endEpoch:
				breakOut = True
				break
		if breakOut:
			break
	print(f"Comments: {count}, commenters: {len(commenters)}")
	return commenters


totalCommenters = defaultdict(int)
overlapCommenters = defaultdict(int)
for subreddit in subreddits:
	commenters = countCommenters(subreddit)

	if not len(overlapCommenters):
		print("Building first")
		for commenter in commenters:
			if commenters[commenter] >= min_comments_per_sub:
				overlapCommenters[commenter] += commenters[commenter]
				totalCommenters[commenter] += commenters[commenter]
		print(f"Done, size: {len(overlapCommenters)}")
	else:
		print(f"Building, current size: {len(overlapCommenters)}")
		newOverlap = defaultdict(int)
		for commenter in commenters:
			if commenters[commenter] >= min_comments_per_sub:
				totalCommenters[commenter] += commenters[commenter]
				if commenter in overlapCommenters:
					newOverlap[commenter] += commenters[commenter]
		overlapCommenters = newOverlap
		print(f"Done, new size: {len(overlapCommenters)}, total commenters: {len(totalCommenters)}")


print(f"{len(overlapCommenters)} of {len(totalCommenters)} total commenters commented in all subreddits, that's {round((len(overlapCommenters) / len(totalCommenters)) * 100, 2)} percent")

with open(file_name, 'w') as txt:
	if sort_by == 'author':
		print(f"Printing to {file_name} sorted by author")
		for user in sorted(overlapCommenters.keys(), key=str.lower):
			txt.write(f"{user}: {overlapCommenters[user]}\n")
	elif sort_by == 'comments':
		print(f"Printing to {file_name} sorted by number of comments")
		for user, comments in sorted(overlapCommenters.items(), key=lambda item: item[1], reverse=True):
			txt.write(f"{user}: {comments}\n")
	else:
		print(f"Printing to {file_name} unsorted")
		for user in overlapCommenters:
			txt.write(f"{user}: {overlapCommenters[user]}\n")
