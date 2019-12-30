import requests
from datetime import datetime
import traceback
import praw
import discord_logging

log = discord_logging.init_logging()

usernames = [
	'SeagullNo1Fan_No1Fan',
	'Toshiro46',
	'Kspehik'
]

url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&subreddit={}&author={}&before="

start_time = datetime.utcnow()


def countObjects(object_type, username, subreddit):
	count = 0
	previous_epoch = int(start_time.timestamp())
	while True:
		new_url = url.format(object_type, subreddit, username)+str(previous_epoch)
		json = requests.get(new_url, headers={'User-Agent': "Stat finder by /u/Watchful1"})
		json_data = json.json()
		if 'data' not in json_data:
			break
		objects = json_data['data']
		if len(objects) == 0:
			break

		for object in objects:
			previous_epoch = object['created_utc'] - 1
			count += 1

	return count

for username in usernames:
	countComments = countObjects("comment", username, "competitiveoverwatch")
	countSubmissions = countObjects("submission", username, "competitiveoverwatch")
	countTmz = countObjects("comment", username, "overwatchtmz")
	log.info(f"{countComments}	{countSubmissions}	{countTmz}")
