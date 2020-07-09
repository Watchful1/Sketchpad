import time
import requests
from datetime import datetime, timedelta
import discord_logging

log = discord_logging.init_logging()

url = "https://api.pushshift.io/reddit/submission/search?limit=1000&sort=desc&subreddit=competitiveoverwatch&before="

start_time = datetime.utcnow()
end_time = start_time - timedelta(days=30)

count = 0
previous_epoch = int(start_time.timestamp())
break_out = False
output = open('posts.txt', 'w')
while True:
	new_url = url + str(previous_epoch)
	json_data = requests.get(new_url, headers={'User-Agent': "Post lister by /u/Watchful1"}).json()
	time.sleep(0.8)
	if 'data' not in json_data:
		break
	objects = json_data['data']
	if len(objects) == 0:
		break

	for object in objects:
		if datetime.utcfromtimestamp(object['created_utc']) < end_time:
			break_out = True
			break

		output.write(f"{object['full_link'].encode(encoding='ascii', errors='ignore').decode()}	{object['title'].encode(encoding='ascii', errors='ignore').decode()}\n")

		previous_epoch = object['created_utc'] - 1
		count += 1

	if break_out:
		break

output.close()
