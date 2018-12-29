import requests
from collections import defaultdict
from datetime import datetime

firstSubreddit = 'redditdev'
secondSubreddit = 'requestabot'

url = "https://api.pushshift.io/reddit/comment/search?&limit=1000&sort=desc&subreddit={}&before="

startTime = datetime.utcnow()


def countCommenters(subreddit):
	count = 0
	commenters = defaultdict(int)
	previousEpoch = int(startTime.timestamp())
	print(f"Counting commenters in: {subreddit}")
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
		print("Comments: {}, {}".format(count, datetime.fromtimestamp(previousEpoch).strftime("%Y-%m-%d")))
	print(f"Comments: {count}, commenters: {len(commenters)}")
	return commenters, count


firstSubredditCommenters, firstSubredditCommentCount = countCommenters(firstSubreddit)
secondSubredditCommenters, secondSubredditCommentCount = countCommenters(secondSubreddit)

print("Comparing commenter lists")
overlapCommenters = set()
totalCommenters = set()
for commenter in firstSubredditCommenters:
	totalCommenters.add(commenter)
	if commenter in secondSubredditCommenters:
		overlapCommenters.add(commenter)
for commenter in secondSubredditCommenters:
	if commenter not in totalCommenters:
		totalCommenters.add(commenter)

print(f"{len(overlapCommenters)} of {len(totalCommenters)} total commenters commented in both subreddits, that's {round((len(overlapCommenters) / len(totalCommenters)) * 100, 2)} percent")
print(f"{firstSubreddit} has {len(firstSubredditCommenters)} commenters, {round((len(overlapCommenters) / len(firstSubredditCommenters)) * 100, 2)} percent commented in {secondSubreddit}")
print(f"{secondSubreddit} has {len(secondSubredditCommenters)} commenters, {round((len(overlapCommenters) / len(secondSubredditCommenters)) * 100, 2)} percent commented in {firstSubreddit}")

with open("users.txt", 'w') as txt:
	for user in overlapCommenters:
		txt.write(user)
		txt.write("\n")
