import json
import base64
import zlib
import re
import os
import sys
from datetime import datetime

subreddit = "SubTestBot1"
original_input_filename = "input.txt"
csv_filename = "notes.csv"
output_filename = "output.txt"

if not os.path.isfile(original_input_filename):
	print(f"Input file {original_input_filename} is missing, please copy it down from the subreddit again")
	sys.exit()

with open(original_input_filename, 'r') as input_file:
	text = input_file.readline()
	data = json.loads(text)

moderators = {}
for i, moderator in enumerate(data["constants"]["users"]):
	moderators[moderator] = i
reasons = {}
for i, reason in enumerate(data["constants"]["warnings"]):
	if reason is None:
		reason = "None"
	reasons[reason] = i

users = {}
note_count = 0
with open(csv_filename, 'r') as csv_file:
	for line in csv_file:
		note_count += 1
		items = line.strip().split(",")
		username = items[0]
		date_time = datetime.strptime(items[1], "%Y-%m-%d %H:%M:%S")
		if items[2] in moderators:
			moderator = moderators[items[2]]
		else:
			print(f"Adding new moderator to list: {items[2]}")
			data["constants"]["users"].append(items[2])
			moderators[items[2]] = len(data["constants"]["users"]) - 1
		reason_string = items[3]
		if items[3] in reasons:
			reason = reasons[items[3]]
		else:
			print(f"Adding new reason to list: {items[3]}")
			data["constants"]["warnings"].append(items[3])
			reasons[items[3]] = len(data["constants"]["warnings"]) - 1
		if items[4] is not None:
			groups = re.search(r'(?:comments/)(\w{3,8})(?:/_/)(\w{3,8})', items[4], flags=re.IGNORECASE)
			if groups:
				link_id = groups.group(1)
				comment_id = groups.group(2)
				link = f"l,{link_id},{comment_id}"
			else:
				groups = re.search(r'(?:comments/)(\w{3,8})', items[4], flags=re.IGNORECASE)
				if groups:
					link_id = groups.group(1)
					link = f"l,{link_id}"
				else:
					groups = re.search(r'(?:message/messages/)(\w{3,8})', items[4], flags=re.IGNORECASE)
					if groups:
						message_id = groups.group(1)
						link = f"m,{message_id}"
					else:
						link = items[4]
		else:
			link = ""
		note_text = items[5]

		note = {
			'n': note_text,
			't': int(date_time.timestamp()),
			'm': moderator,
			'l': link,
			'w': reason
		}
		if username in users:
			users[username]['ns'].append(note)
		else:
			users[username] = {'ns': [note]}

print(f"Loaded {note_count} notes across {len(users)} users")

output_dict = {
	"ver": data["ver"],
	"constants": {
		"users": data["constants"]["users"],
		"warnings": data["constants"]["warnings"]
	}
}

blob = json.dumps(users).encode()
compressed_blob = zlib.compress(blob)
encoded_blob = base64.b64encode(compressed_blob).decode()
output_dict['blob'] = str(encoded_blob)
with open(output_filename, 'w') as output_file:
	output_file.write(json.dumps(output_dict))

print(f"Dumped out to {output_filename}. Copy that back to https://www.reddit.com/r/{subreddit}/wiki/edit/usernotes")
print(f"You may need to go to the toolbox settings and click 'Clear your cache' before you can see the changes")
