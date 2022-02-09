import requests
from datetime import datetime, timedelta
import time
import json
import praw
from collections import defaultdict

reddit = praw.Reddit("Watchful1BotTest")

subreddit = "bayarea"
url = "https://api.pushshift.io/reddit/submission/search?limit=1000&sort=desc&subreddit={}&before="

start_time = datetime.utcnow()
end_time = start_time - timedelta(days=180)
previous_epoch = int(start_time.timestamp())
post_ids = []
break_out = False
while True:
	new_url = url.format(subreddit) + str(previous_epoch)
	json_text = requests.get(new_url, headers={'User-Agent': "Post downloader by /u/Watchful1"})
	time.sleep(1)
	try:
		json_data = json_text.json()
	except json.decoder.JSONDecodeError:
		time.sleep(1)
		continue

	if 'data' not in json_data:
		break
	objects = json_data['data']
	if len(objects) == 0:
		break

	for item in objects:
		if datetime.utcfromtimestamp(item['created_utc']) < end_time:
			break_out = True
			break
		previous_epoch = item['created_utc'] - 1
		post_ids.append("t3_"+item['id'])
		# if 'link_flair_text' in item:
		# 	flairs[item['link_flair_text']] += 1

	if break_out:
		break


flairs = defaultdict(int)
for post in reddit.info(post_ids):
	flairs[post.link_flair_text] += 1

for flair, count in flairs.items():
	print(f"{flair}: {count}")
