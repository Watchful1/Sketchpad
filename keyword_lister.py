import requests
from datetime import datetime, timedelta

subreddit = "cats"
keyword = "doggie"
days_to_search = 7

url = "https://api.pushshift.io/reddit/comment/search/?limit=1000&sort=desc&subreddit={}&q={}&before={}"
previousEpoch = int(datetime.utcnow().timestamp())
endEpoch = int((datetime.utcnow() - timedelta(days=days_to_search)).timestamp())
breakOut = False
output_file = open("output.txt", 'w')
while True:
	url = url.format(subreddit, keyword, str(previousEpoch))
	comments = requests.get(url.format(subreddit, keyword, str(previousEpoch)), headers={'User-Agent': "keyword counter"}).json()['data']
	if len(comments) == 0:
		break
	for comment in comments:
		previousEpoch = comment['created_utc'] - 1
		output_file.write(f"{comment['author']} : {datetime.utcfromtimestamp(comment['created_utc']).strftime('%Y-%m-%d %H:%M:%S')}\n")
		if previousEpoch < endEpoch:
			breakOut = True
			break
	if breakOut:
		break
output_file.close()
