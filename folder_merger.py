import discord_logging
import os
import hashlib
from collections import defaultdict
from pathlib import Path

log = discord_logging.init_logging(debug=True)

def hash_file(file_name):
	h = hashlib.md5()
	with open(file_name,'rb') as file:
		chunk = 0
		while chunk != b'':
			chunk = file.read(1024)
			h.update(chunk)
	return h.hexdigest()


def scan_save_hashes(base, folder):
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


def try_load_hashes(base, folder):
	hashes_file_path = os.path.join(base, f"{folder}.txt")
	if not os.path.exists(hashes_file_path):
		return None

	hashes_file = open(os.path.join(base, f"{folder}.txt"), 'r', encoding="utf-8")
	files = []
	for line in hashes_file:
		path, file_hash = line.split("\t")
		full_path = os.path.join(base, folder, path)
		file_type = Path(full_path).suffix
		if len(file_type) == 0:
			file_type = None
		else:
			file_type = file_type[1:]
		files.append((folder, path, file_hash, file_type))

	return files



if __name__ == "__main__":
	base = r"\\MYCLOUDPR4100\Public\asstr"
	#folders = ["mirror", "torrent", "wayback", "xyz_1", "xyz_2", "xyz_3"]
	folders = ["xyz_2", "xyz_3"]

	all_files = defaultdict(list)
	all_folders = {}
	for folder in folders:
		log.info(f"Trying to load hashes for {folder}")
		files = try_load_hashes(base, folder)
		if files is None:
			log.info(f"Failed to load hashes for {folder}, scanning")
			scan_save_hashes(base, folder)
			files = try_load_hashes(base, folder)
		log.info(f"Finished loading hashes for {folder}. {len(files)} hashes loaded")
		all_folders[folder] = files

		for folder2, path, file_hash, file_type in files:
			all_files[file_hash].append((folder2, path, file_hash, file_type))


	for folder in all_folders.keys():
		matched_hashes, total_hashes = 0, 0
		for folder2, path, file_hash, file_type in all_folders[folder]:
			if len(all_files[file_hash]) > 1:
				matched_hashes += 1
			total_hashes += 1
		log.info(f"{folder}: {matched_hashes} matched, {total_hashes} total")


