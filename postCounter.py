import requests
from datetime import datetime
from datetime import timedelta

subreddit = 'reddeadredemption'
lookback_hours = 24

types = ['comment', 'submission']
url = "https://api.pushshift.io/reddit/{}/search?&limit=1000&sort=desc&subreddit={}&before="

startTime = datetime.utcnow()
endTime = startTime - timedelta(hours=lookback_hours)
endEpoch = int(endTime.timestamp())

for type in types:
	count = 0
	breakOut = False
	previousEpoch = int(startTime.timestamp())
	while True:
		newUrl = url.format(type, subreddit)+str(previousEpoch)
		json = requests.get(newUrl, headers={'User-Agent': "Object counter by /u/Watchful1"})
		objects = json.json()['data']
		for object in objects:
			previousEpoch = object['created_utc'] - 1
			if previousEpoch < endEpoch:
				breakOut = True
				break
			count += 1

		if breakOut:
			print(f"{count} {type}s")
			break

