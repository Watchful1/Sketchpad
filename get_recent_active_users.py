import time
import discord_logging
import requests
from datetime import datetime, timedelta
from collections import defaultdict

log = discord_logging.init_logging()

if __name__ == "__main__":
	url = "https://api.pushshift.io/reddit/comment/search?limit=1000&sort=desc&subreddit=competitiveoverwatch&before="

	start_time = datetime.utcnow()
	end_time = start_time - timedelta(days=30*6)

	count = 0
	previous_epoch = int(start_time.timestamp())
	break_out = False
	commenters = defaultdict(int)
	while True:
		new_url = url + str(previous_epoch)
		try:
			json_data = requests.get(new_url, headers={'User-Agent': "User counter by /u/Watchful1"}).json()
		except requests.exceptions.ConnectionError:
			time.sleep(5)
			log.info(f"Connection error, sleeping")
			continue
		time.sleep(0.8)
		if 'data' not in json_data:
			break
		data = json_data['data']
		if len(data) == 0:
			break

		for comment in data:
			if datetime.utcfromtimestamp(comment['created_utc']) < end_time:
				break_out = True
				break

			commenters[comment['author']] += 1

			previous_epoch = comment['created_utc'] - 1
			count += 1
			if count % 1000 == 0:
				log.info(f"{datetime.utcfromtimestamp(comment['created_utc']).strftime('%Y-%m-%d')}")

		if break_out:
			break
	log.info(f"Done with users. Found {len(commenters)} through {datetime.utcfromtimestamp(previous_epoch).strftime('%Y-%m-%d')}")

	with open('commenters.txt', 'w') as output:
		for commenter, count_comments in reversed(sorted(commenters.items(), key=lambda item: item[1])):
			output.write(f"{commenter}	{count_comments}\n")
