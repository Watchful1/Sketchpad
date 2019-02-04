import requests
from datetime import datetime
from datetime import timezone
from collections import defaultdict
from wordcloud import WordCloud

subreddit = "nfl"

url = "https://api.pushshift.io/reddit/comment/search?limit=1000&sort=desc&subreddit={}&before="

threads_whitelist = {
	't3_amtn1j': "pre game",
	't3_amv7iw': "first half",
	't3_amw90u': "half time",
	't3_amwa81': "second half",
	't3_amx9iz': "post game",
	't3_amv7hz': "commercials",
}

start_time = datetime.now(timezone.utc)

end_time = datetime.strptime("2019-02-03 12:30:00 UTC", "%Y-%m-%d %H:%M:%S %Z")
end_epoch = int(end_time.timestamp())


count = 0
previous_epoch = int(start_time.timestamp())
processed_comments = set()
threads = defaultdict(int)
minute_buckets = []
current_minute = start_time.minute
comments_in_minute = 0
words_in_minute = []
while True:
	new_url = url.format(subreddit)+str(previous_epoch)
	json = requests.get(new_url, headers={'User-Agent': "Comment graph by /u/Watchful1"})
	json_data = json.json()
	if 'data' not in json_data:
		break
	comments = json_data['data']
	if len(comments) == 0:
		break

	for comment in comments:
		previous_epoch = comment['created_utc'] + 1

		if comment['id'] in processed_comments:
			continue

		if comment['link_id'] not in threads_whitelist:
			continue

		count += 1
		processed_comments.add(comment['id'])

		created_datetime = datetime.fromtimestamp(comment['created_utc'])
		if current_minute != created_datetime.minute:
			minute_buckets.append("{},{}".format(created_datetime.strftime("%I:%M"), comments_in_minute))

			wordcloud = WordCloud().generate(' '.join(words_in_minute))
			wordcloud.to_file("clouds/{}-{}.png".format(created_datetime.strftime("%I-%M"), comments_in_minute))

			comments_in_minute = 0
			current_minute = created_datetime.minute
			words_in_minute = []
		comments_in_minute += 1
		words_in_minute.append(comment['body'])

		threads[comment['link_id']] += 1

	print("Processed {} through {}".format(count, datetime.fromtimestamp(previous_epoch).strftime("%Y-%m-%d %H:%M:%S")))

	if previous_epoch < end_epoch:
		print(f"Finished: {previous_epoch} : {end_epoch}")
		break

		#datetime.fromtimestamp(comment['created_utc']).strftime("%Y-%m-%d")

for thread in threads:
	if thread in threads_whitelist:
		print(f"{threads_whitelist[thread]}: {threads[thread]}")

for minute in minute_buckets[::-1]:
	print(minute)
