import discord_logging
import os
import hashlib
from collections import defaultdict

log = discord_logging.init_logging(debug=True)

def hash_file(file_name):
	h = hashlib.md5()
	with open(file_name,'rb') as file:
		chunk = 0
		while chunk != b'':
			chunk = file.read(1024)
			h.update(chunk)
	return h.hexdigest()


if __name__ == "__main__":
	base = r"\\MYCLOUDPR4100\Public\asstr"
	#folders = ["torrent", "wayback", "xyz_1", "xyz_2", "xyz_3"]
	folders = ["wayback", "xyz_1", "xyz_2", "xyz_3"]

	for folder in folders:
		path = os.path.join(base, folder)
		paths_file = open(os.path.join(base, f"{folder}.txt"), 'w', encoding="utf-8")

		count_files = 0
		for root, sub_dirs, files in os.walk(path):
			for filename in files:
				count_files += 1
				if root == path:
					relative_path = filename
				else:
					relative_path = os.path.join(root[len(path) + 1:], filename)
				file_hash = hash_file(os.path.join(root, filename))
				paths_file.write(f"{relative_path}	{file_hash}\n")
				if count_files % 1000 == 0:
					log.info(f"{folder}: {count_files:,}")

		log.info(f"{folder}: {count_files:,}")
		paths_file.close()
