import requests
from datetime import datetime, timedelta
import time
import praw
import discord_logging

log = discord_logging.init_logging()

usernames = [
"sdadadasdsad",
"ImmediateWait",
"Caleb10E",
"Jamezbar",
"Simbasdead",
"Aquagirl3212",
"N3cropolis",
]

url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&subreddit={}&author={}&before="

start_time = datetime.utcnow()
end_time = start_time - timedelta(days=30 * 6)


def countObjects(object_type, username, subreddit):
	count = 0
	previous_epoch = int(start_time.timestamp())
	break_out = False
	while True:
		new_url = url.format(object_type, subreddit, username)+str(previous_epoch)
		json_data = requests.get(new_url, headers={'User-Agent': "Stat finder by /u/Watchful1"}).json()
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

			previous_epoch = object['created_utc'] - 1
			count += 1

		if break_out:
			break

	return count


r = praw.Reddit("Watchful1BotTest")

for username in usernames:
	countComments = countObjects("comment", username, "competitiveoverwatch")
	countSubmissions = countObjects("submission", username, "competitiveoverwatch")
	countTmz = countObjects("comment", username, "overwatchtmz")

	user = r.redditor(username)
	account_age = (start_time - datetime.utcfromtimestamp(user.created_utc)).days / 365
	subreddits = [f"r/{sub.display_name}" for sub in user.moderated()]

	print(f"{account_age:.1f}	{countComments}	{countSubmissions}	{countTmz}	{', '.join(subreddits)}")
