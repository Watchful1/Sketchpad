import discord_logging
import csv
from datetime import datetime
from collections import defaultdict

log = discord_logging.init_logging()

if __name__ == "__main__":
	pixel_map = defaultdict(lambda: defaultdict(set))
	usernames = set()
	pixel_count = 0
	with open(r"C:\Users\greg\Desktop\Place\pixels.csv", 'r') as pixels:
		for line in pixels:
			coord, timestamp, username = line.strip().split(",")
			pixel_map[coord][int(timestamp)].add(username)
			usernames.add(username)
			pixel_count += 1
			if pixel_count % 1000000 == 0:
				log.info(f"{pixel_count:,} : {len(usernames):,}")
			if pixel_count >= 15000000:
				log.info(f"{pixel_count:,} : {len(usernames):,}")
				break

	mapped_usernames = {}
	with open(r"C:\Users\greg\Desktop\Place\2022_place_canvas_history.csv", 'r') as csvfile:
		reader = csv.reader(csvfile)
		next(reader)  # skip headers
		lines = 1
		matching_lines = 0
		epoch = datetime.utcfromtimestamp(0)
		differences = defaultdict(int)
		with open(r"C:\Users\greg\Desktop\Place\matching.txt", 'w') as output:
			for row in reader:
				try:
					timestamp = int((datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S.%f UTC') - epoch).total_seconds() * 1000.0)
				except ValueError:
					timestamp = int((datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S UTC') - epoch).total_seconds() * 1000.0)
				user_hash = row[1]
				coord = row[3].replace(",", "x")
				if coord in pixel_map:
					timestamp_map = pixel_map[coord]
					if timestamp in timestamp_map:
						user_list = timestamp_map[timestamp]
						if len(user_list) == 1:
							mapped_usernames[min(user_list)] = user_hash
							matching_lines += 1
						elif len(user_list) > 1:
							log.info(','.join(user_list))
					else:
						last_digits = timestamp % 1000
						for each_timestamp in timestamp_map:
							if each_timestamp % 1000 == last_digits:
								differences[timestamp - each_timestamp] += 1
								#log.info(f"{timestamp} : {each_timestamp} : {timestamp - each_timestamp}")

				lines += 1
				if lines % 1000000 == 0:
					log.info(f"{row[0]}: {lines:,} : {matching_lines:,}")
					largest_diff = 1
					diff_count = 1
					for difference, count in differences.items():
						if count > diff_count:
							largest_diff = difference
							diff_count = count
					log.info(f"{largest_diff} : {diff_count}")

	log.info(f"{row[0]}: {lines:,} : {matching_lines:,}")

	with open(r"C:\Users\greg\Desktop\Place\user_map.txt", 'w') as output:
		for username, user_hash in mapped_usernames.items():
			output.write(f"{username}	{user_hash}\n")
