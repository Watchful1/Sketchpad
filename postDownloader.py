import requests
from datetime import datetime
import traceback
import time
import json
import sys

username = ""  # put the username you want to download in the quotes
subreddit = "egg_irl"  # put the subreddit you want to download in the quotes
# leave either one blank to download an entire user's or subreddit's history
# or fill in both to download a specific users history from a specific subreddit

convert_to_ascii = False  # don't touch this unless you know what you're doing

filter_string = None
if username == "" and subreddit == "":
	print("Fill in either username or subreddit")
	sys.exit(0)
elif username == "" and subreddit != "":
	filter_string = f"subreddit={subreddit}"
elif username != "" and subreddit == "":
	filter_string = f"author={username}"
else:
	filter_string = f"author={username}&subreddit={subreddit}"

url = "https://api.pushshift.io/reddit/{}/search?limit=1000&order=desc&{}&before="

start_time = datetime.utcnow()  #datetime.strptime("10/05/2021", "%m/%d/%Y")
end_time = None  #datetime.strptime("09/25/2021", "%m/%d/%Y")#datetime.utcnow()


def downloadFromUrl(filename, object_type):
	print(f"Saving {object_type}s to {filename}")

	count = 0
	if convert_to_ascii:
		handle = open(filename, 'w', encoding='ascii')
	else:
		handle = open(filename, 'w', encoding='UTF-8')
	previous_epoch = int(start_time.timestamp())
	break_out = False
	while True:
		new_url = url.format(object_type, filter_string)+str(previous_epoch)
		json_text = requests.get(new_url, headers={'User-Agent': "Post downloader by /u/Watchful1"})
		time.sleep(1)  # pushshift has a rate limit, if we send requests too fast it will start returning error messages
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

		for object in objects:
			previous_epoch = object['created_utc'] - 1
			if end_time is not None and datetime.utcfromtimestamp(previous_epoch) < end_time:
				break_out = True
				break
			count += 1
			if object_type == 'comment':
				try:
					handle.write(str(object['score']))
					handle.write(" : ")
					handle.write(datetime.fromtimestamp(object['created_utc']).strftime("%Y-%m-%d"))
					handle.write(" : u/")
					handle.write(object['author'])
					handle.write(" : ")
					handle.write(f"https://www.reddit.com{object['permalink']}")
					handle.write("\n")
					if convert_to_ascii:
						handle.write(object['body'].encode(encoding='ascii', errors='ignore').decode())
					else:
						handle.write(object['body'])
					handle.write("\n-------------------------------\n")
				except Exception as err:
					print(f"Couldn't print comment: https://www.reddit.com{object['permalink']}")
					print(traceback.format_exc())
			elif object_type == 'submission':
				try:
					handle.write(str(object['score']))
					handle.write(" : ")
					handle.write(datetime.fromtimestamp(object['created_utc']).strftime("%Y-%m-%d"))
					handle.write(" : ")
					if convert_to_ascii:
						handle.write(object['title'].encode(encoding='ascii', errors='ignore').decode())
					else:
						handle.write(object['title'])
					handle.write(" : u/")
					handle.write(object['author'])
					handle.write(" : ")
					handle.write(f"https://www.reddit.com{object['permalink']}")
					handle.write("\n")
					if object['is_self']:
						if 'selftext' in object:
							if convert_to_ascii:
								handle.write(object['selftext'].encode(encoding='ascii', errors='ignore').decode())
							else:
								handle.write(object['selftext'])
					else:
						handle.write(object['url'])

					handle.write("\n-------------------------------\n")
				except Exception as err:
					print(f"Couldn't print post: {object['url']}")
					print(traceback.format_exc())

		if break_out:
			break

		print("Saved {} {}s through {}".format(count, object_type, datetime.fromtimestamp(previous_epoch).strftime("%Y-%m-%d")))

	print(f"Saved {count} {object_type}s")
	handle.close()


downloadFromUrl("posts.txt", "submission")
downloadFromUrl("comments.txt", "comment")
