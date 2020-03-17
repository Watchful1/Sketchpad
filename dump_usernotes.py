import json
import base64
import zlib
import os
import sys
from datetime import datetime

subreddit = "CompetitiveOverwatch"
input_filename = "input.txt"
csv_filename = "notes.csv"

if os.path.isfile(input_filename):
	print(f"Reading from: {input_filename}")
else:
	open(input_filename, 'a').close()
	print(f"I created the empty file: {input_filename}")
	print(
		f"Please go to https://www.reddit.com/r/{subreddit}/wiki/edit/usernotes and copy the text into that file, "
		f"save it and run this program again")
	sys.exit()

try:
	with open(input_filename, 'r') as input_file:
		text = input_file.readline()
		data = json.loads(text)
		if "ver" not in data or "constants" not in data or "blob" not in data:
			print("Something is missing in the data, are you sure you copied the whole thing?")
			sys.exit()
		if data["ver"] != 6:
			print(f"This tool was built for usernotes version 6, but this is version {data['ver']}")
			sys.exit()
except Exception as err:
	print(
		f"Something went wrong reading the input file. Make sure you've copied all of"
		f"https://www.reddit.com/r/{subreddit}/wiki/edit/usernotes")
	print(err)
	sys.exit()

mods = data["constants"]["users"]
warnings = data["constants"]["warnings"]
blob = data["blob"]
decoded = base64.b64decode(blob)
raw = zlib.decompress(decoded)
parsed = json.loads(raw)

user_count = 0
note_count = 0
with open(csv_filename, 'w') as csv_file:
	for username in parsed:
		user_count += 1
		for notes in parsed[username]["ns"]:
			note_count += 1
			note = notes["n"]

			link = ''
			link_raw = notes["l"]
			if link_raw:
				if "reddit.com" in link_raw:
					link = link_raw
				else:
					link_array = link_raw.split(",")
					if link_array[0] == "l":
						if len(link_array) == 3:
							link = f"https://www.reddit.com/r/{subreddit}/comments/{link_array[1]}/_/{link_array[2]}"
						elif len(link_array) == 2:
							link = f"https://www.reddit.com/r/{subreddit}/comments/{link_array[1]}/"
					elif link_array[0] == "m":
						link = f"https://www.reddit.com/message/messages/{link_array[1]}/"

			time = datetime.utcfromtimestamp(notes["t"]).strftime("%Y-%m-%d %H:%M:%S")
			mod = mods[notes["m"]]
			reason = warnings[notes["w"]]

			csv_file.write(f"{username},{time},{mod},{reason},{link},{note}\n")

print(f"Parsed {note_count} notes across {user_count} users and wrote out {csv_filename}")
