import requests
from datetime import datetime, timedelta
import time
import praw
import discord_logging
from collections import defaultdict

log = discord_logging.init_logging()

usernames = [
"ModWilliam",
]

count_url = "https://api.pushshift.io/reddit/{}/search?limit=1000&sort=desc&subreddit={}&author={}&before="
periods_url = "https://api.pushshift.io/reddit/comment/search?limit=1000&sort=desc&author={}&before="

start_time = datetime.utcnow()
end_time = start_time - timedelta(days=30 * 6)


def countObjects(object_type, username, subreddit):
	count = 0
	previous_epoch = int(start_time.timestamp())
	break_out = False
	while True:
		new_url = count_url.format(object_type, subreddit, username)+str(previous_epoch)
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


def timePeriods(username):
	previous_epoch = int(start_time.timestamp())
	break_out = False
	hours = defaultdict(int)
	offset = 4
	while True:
		new_url = periods_url.format(username)+str(previous_epoch)
		json_data = requests.get(new_url, headers={'User-Agent': "Stat finder by /u/Watchful1"}).json()
		time.sleep(0.8)
		if 'data' not in json_data:
			break
		objects = json_data['data']
		if len(objects) == 0:
			break

		for object in objects:
			object_time = datetime.utcfromtimestamp(object['created_utc'])
			if object_time < end_time:
				break_out = True
				break

			hours[object_time.hour + offset] += 1

			previous_epoch = object['created_utc'] - 1

		if break_out:
			break

	night_est = 0
	morning_est = 0
	afternoon_est = 0
	evening_est = 0
	for hour in range(0, 6):
		night_est += hours[hour]
	for hour in range(7, 12):
		morning_est += hours[hour]
	for hour in range(13, 18):
		afternoon_est += hours[hour]
	for hour in range(19, 24):
		evening_est += hours[hour]
	print(f"{night_est}:{morning_est}:{afternoon_est}:{evening_est}")


r = praw.Reddit("Watchful1BotTest")

for username in usernames:
	countComments = countObjects("comment", username, "competitiveoverwatch")
	countSubmissions = countObjects("submission", username, "competitiveoverwatch")
	countTmz = countObjects("comment", username, "overwatchtmz")

	user = r.redditor(username)
	account_age = (start_time - datetime.utcfromtimestamp(user.created_utc)).days / 365
	subreddits = [f"r/{sub.display_name}" for sub in user.moderated()]

	print(f"{account_age:.1f}	{countComments}	{countSubmissions}	{countTmz}	{', '.join(subreddits)}")

	#timePeriods(username)
