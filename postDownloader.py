import requests
from datetime import datetime
import traceback
import time
import json
import sys
import csv
import json

# IMPORTANT READ THIS FIRST
# The pushshift service that this script uses is only available to moderators. Go through this guide to get a token and update the token field below
# https://api.pushshift.io/guide
token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiV2F0Y2hmdWwxIiwiZXhwaXJlcyI6MTcxMTc2NTA3Miwic2NvcGUiOiIqIn0.L-RXleAg_ncStaAZAOf7oKd1cK8psisM3PENPa-eXVM"

username = "Straight-Wrap-172"  # put the username you want to download in the quotes
subreddit = ""  # put the subreddit you want to download in the quotes
thread_id = ""  # put the id of the thread you want to download in the quotes, it's the first 5 to 7 character string of letters and numbers from the url, like 107xayi
# leave either one blank to download an entire user's or subreddit's history
# or fill in both to download a specific users history from a specific subreddit

# change this to one of "human", "csv" or "json"
# - human: the score, creation date, author, link and then the comment/submission body on a second line. Objects are separated by lines of dashes
# - csv: a comma seperated value file with the fields score, date, title, author, link and then body or url
# - json: the full json object
output_format = "human"

# default start time is the current time and default end time is all history
# you can change out the below lines to set a custom start and end date. The script works backwards, so the end date has to be before the start date
start_time = datetime.utcnow()  #datetime.strptime("10/05/2021", "%m/%d/%Y")
end_time = None  #datetime.strptime("01/01/2023", "%m/%d/%Y")

convert_to_ascii = False  # don't touch this unless you know what you're doing
convert_thread_id_to_base_ten = True  # don't touch this unless you know what you're doing


def write_human_line(handle, obj, is_submission, convert_to_ascii):
	handle.write(str(obj['score']))
	handle.write(" : ")
	handle.write(datetime.fromtimestamp(obj['created_utc']).strftime("%Y-%m-%d"))
	if is_submission:
		handle.write(" : ")
		if convert_to_ascii:
			handle.write(obj['title'].encode(encoding='ascii', errors='ignore').decode())
		else:
			handle.write(obj['title'])
	handle.write(" : u/")
	handle.write(obj['author'])
	handle.write(" : ")
	if 'permalink' not in obj:
		handle.write(f"No link available")
	else:
		handle.write(f"https://www.reddit.com{obj['permalink']}")
	handle.write("\n")
	if is_submission:
		if obj['is_self']:
			if 'selftext' in obj:
				if convert_to_ascii:
					handle.write(obj['selftext'].encode(encoding='ascii', errors='ignore').decode())
				else:
					handle.write(obj['selftext'])
		else:
			handle.write(obj['url'])
	else:
		if convert_to_ascii:
			handle.write(obj['body'].encode(encoding='ascii', errors='ignore').decode())
		else:
			handle.write(obj['body'])
	handle.write("\n-------------------------------\n")


def write_csv_line(writer, obj, is_submission):
	output_list = []
	output_list.append(str(obj['score']))
	output_list.append(datetime.fromtimestamp(obj['created_utc']).strftime("%Y-%m-%d"))
	if is_submission:
		output_list.append(obj['title'])
	output_list.append(f"u/{obj['author']}")
	output_list.append(f"https://www.reddit.com{obj['permalink']}")
	if is_submission:
		if obj['is_self']:
			if 'selftext' in obj:
				output_list.append(obj['selftext'])
			else:
				output_list.append("")
		else:
			output_list.append(obj['url'])
	else:
		output_list.append(obj['body'])
	writer.writerow(output_list)


def write_json_line(handle, obj):
	handle.write(json.dumps(obj))
	handle.write("\n")


def download_from_url(filename, url_base, output_format, start_datetime, end_datetime, is_submission, convert_to_ascii):
	print(f"Saving to {filename}")

	count = 0
	if output_format == "human" or output_format == "json":
		if convert_to_ascii:
			handle = open(filename, 'w', encoding='ascii')
		else:
			handle = open(filename, 'w', encoding='UTF-8')
	else:
		handle = open(filename, 'w', encoding='UTF-8', newline='')
		writer = csv.writer(handle)

	previous_epoch = int(start_datetime.timestamp())
	break_out = False
	while True:
		new_url = url_base+str(previous_epoch)
		json_text = requests.get(new_url, headers={'User-Agent': "Post downloader by /u/Watchful1", 'Authorization': f"Bearer {token}"})
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

		for obj in objects:
			previous_epoch = obj['created_utc'] - 1
			if end_datetime is not None and datetime.utcfromtimestamp(previous_epoch) < end_datetime:
				break_out = True
				break
			count += 1
			try:
				if output_format == "human":
					write_human_line(handle, obj, is_submission, convert_to_ascii)
				elif output_format == "csv":
					write_csv_line(writer, obj, is_submission)
				elif output_format == "json":
					write_json_line(handle, obj)
			except Exception as err:
				if 'permalink' in obj:
					print(f"Couldn't print object: https://www.reddit.com{obj['permalink']}")
				else:
					print(f"Couldn't print object, missing permalink: {obj['id']}")
				print(err)
				print(traceback.format_exc())

		if break_out:
			break

		print(f"Saved {count} through {datetime.fromtimestamp(previous_epoch).strftime('%Y-%m-%d')}")

	print(f"Saved {count}")
	handle.close()


if __name__ == "__main__":
	filter_string = None
	if username == "" and subreddit == "" and thread_id == "":
		print("Fill in username, subreddit or thread id")
		sys.exit(0)
	if output_format not in ("human", "csv", "json"):
		print("Output format must be one of human, csv, json")
		sys.exit(0)

	filters = []
	if username:
		filters.append(f"author={username}")
	if subreddit:
		filters.append(f"subreddit={subreddit}")
	if thread_id:
		if convert_thread_id_to_base_ten:
			filters.append(f"link_id={int(thread_id, 36)}")
		else:
			filters.append(f"link_id=t3_{thread_id}")
	filter_string = '&'.join(filters)

	url_template = "https://api.pushshift.io/reddit/{}/search?limit=1000&order=desc&{}&before="

	if not thread_id:
		download_from_url("posts.txt", url_template.format("submission", filter_string), output_format, start_time, end_time, True, convert_to_ascii)
	download_from_url("comments.txt", url_template.format("comment", filter_string), output_format, start_time, end_time, False, convert_to_ascii)
