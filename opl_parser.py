import discord_logging
import os
import csv
import re
from datetime import datetime
from collections import defaultdict

log = discord_logging.init_logging()

if __name__ == "__main__":
	input_folder = r"C:\Users\greg\Desktop\Place\details"
	file_lines = 0
	pixels = 0
	reg = re.compile(r"p(\d+x\d+).*?lastModifiedTimestamp...([\d.e+]+).*?userID.*?t2_(\w+).*?username.*?([\w\-_]+)")
	with open(r"C:\Users\greg\Desktop\Place\pixels.csv", 'w') as output:
		for subdir, dirs, files in os.walk(input_folder):
			for filename in files:
				with open(os.path.join(subdir, filename), 'r') as csvfile:
					#reader = csv.reader(csvfile)
					for line in csvfile:
						matches = reg.findall(line)
						if matches:
							for match in matches:
								coord = match[0]
								timestamp = int(float(match[1]))
								username = match[3]
								output.write(f"{coord},{timestamp},{username}\n")
								pixels += 1
						file_lines += 1
						if file_lines % 10000 == 0:
							log.info(f"{file_lines:,} : {pixels:,}")



	# with open(r"C:\Users\greg\Desktop\Place\user_hashes.txt", 'w') as output:
	# 	for user_hash, count_pixels in user_hashes.items():
	# 		output.write(f"{user_hash}	{count_pixels}\n")
