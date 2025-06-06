import sys

import requests
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import time
import os
import json

token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiV2F0Y2hmdWwxIiwiZXhwaXJlcyI6MTY5MzY3ODYwMywic2NvcGUiOiIqIn0.FkGaw5m1nt7pP5JbUNNUV4NZ4wocVzhJ1GUYaQJERRU"
subreddit = "competitiveoverwatch"
file_name = "ids.txt"
url = "https://api.pushshift.io/reddit/comment/search?limit=1000&order=desc&subreddit={}&before="

if __name__ == "__main__":
	current_time = datetime.utcnow()  # datetime.strptime("22-02-25 00:00:00", '%y-%m-%d %H:%M:%S')#
	end_time = datetime.strptime("23-01-01 00:00:00", '%y-%m-%d %H:%M:%S') # current_time - timedelta(days=lookback_days)

	break_out = False
	comment_ids = []
	count = 0
	while True:
		newUrl = url.format(subreddit)+str(int(current_time.replace(tzinfo=timezone.utc).timestamp()))
		try:
			response = requests.get(newUrl, headers={'User-Agent': "Overlap counter by /u/Watchful1", 'Authorization': f"Bearer {token}"})
		except (requests.exceptions.ReadTimeout, requests.exceptions.ChunkedEncodingError, requests.exceptions.ConnectionError):
			print(f"Pushshift timeout, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
			time.sleep(5)
			continue
		try:
			result_data = response.json()
			if "detail" in result_data and result_data['detail'] == "Not authenticated":
				print("You are not authenticated, read the comment at the top and update the token")
				sys.exit(1)

			objects = result_data['data']
		except json.decoder.JSONDecodeError:
			print(f"Decoding error, this usually means pushshift is down. Waiting 5 seconds and trying again: {newUrl}")
			time.sleep(5)
			continue

		time.sleep(1)  # pushshift is ratelimited. If we go too fast we'll get errors

		if len(objects) == 0:
			break
		for obj in objects:
			current_time = datetime.utcfromtimestamp(obj['created_utc'] - 1)
			comment_ids.append(obj['id'])
			count += 1
			if count % 1000 == 0:
				print(f"{count:,}, {current_time.strftime('%Y-%m-%d')}")
			if current_time < end_time:
				break_out = True
				break
		if break_out:
			break

	print(f"{count:,}, {current_time.strftime('%Y-%m-%d')}")

	with open(file_name, 'w') as txt:
		for comment_id in comment_ids:
			txt.write(comment_id)
			txt.write("\n")
