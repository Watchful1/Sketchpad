import requests
from collections import defaultdict
from datetime import datetime
from datetime import timedelta

subreddits = ['JerkOffToCelebs', 'celebs']
lookback_days = 180

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
		json = requests.get(newUrl, headers={'User-Agent': "Overlap counter by /u/Watchful1"})
		objects = json.json()['data']
		if len(objects) == 0:
			break
		for object in objects:
			previousEpoch = object['created_utc'] - 1
			commenters[object['author']] += 1
			count += 1
			if count % 10000 == 0:
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


totalCommenters = set()
overlapCommenters = set()
for subreddit in subreddits:
	commenters = countCommenters(subreddit)

	if not len(overlapCommenters):
		print("Building first")
		for commenter in commenters:
			overlapCommenters.add(commenter)
			totalCommenters.add(commenter)
	else:
		print(f"Building, current size: {len(overlapCommenters)}")
		newOverlap = set()
		for commenter in commenters:
			totalCommenters.add(commenter)
			if commenter in overlapCommenters:
				newOverlap.add(commenter)
		overlapCommenters = newOverlap
		print(f"Done, new size: {len(overlapCommenters)}")


print(f"{len(overlapCommenters)} of {len(totalCommenters)} total commenters commented in all subreddits, that's {round((len(overlapCommenters) / len(totalCommenters)) * 100, 2)} percent")

with open("users.txt", 'w') as txt:
	for user in overlapCommenters:
		txt.write(user)
		txt.write("\n")
