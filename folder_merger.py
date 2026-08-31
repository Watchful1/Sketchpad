import discord_logging
import os
import sys
import hashlib
from collections import defaultdict
from pathlib import Path

log = discord_logging.init_logging(debug=True)

base = r"\\MYCLOUDPR4100\Public\asstr"


class SourceFile:
	def __init__(self, folder, path, file_hash):
		global base
		self.folder = folder
		self.path = path
		self.file_hash = file_hash

		full_path = Path(os.path.join(base, folder, path))
		file_type = full_path.suffix
		if len(file_type) == 0:
			self.file_type = None
		else:
			self.file_type = file_type[1:]
		self.name = full_path.stem
		self.with_parent = os.path.join(full_path.parent.stem, self.name)

	def get_full_path(self):
		global base
		return os.path.join(base, self.folder, self.path)

	def __str__(self):
		return f"{self.path} : {self.file_hash}"

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
		files.append(SourceFile(folder, path, file_hash.strip()))

	return files


def lookup_exclude(lookup_table, file, key_name):
	key = getattr(file, key_name)
	result_list = lookup_table.get(key)
	if result_list is None:
		return None
	if len(result_list) == 1:
		return None
	excluded_list = []
	for result in result_list:
		if result.folder != file.folder:
			excluded_list.append(result)
	return excluded_list


if __name__ == "__main__":
	base = r"\\MYCLOUDPR4100\Public\asstr"
	folders = ["mirror", "mirror2", "torrent", "wayback", "xyz_1", "xyz_2", "xyz_3", "ftp"]
	#folders = ["xyz_1", "xyz_2", "xyz_3"]

	files_by_hash = defaultdict(list)
	files_by_name = defaultdict(list)
	files_by_with_parent = defaultdict(list)
	files_by_path = defaultdict(list)
	all_files_by_folder = {}
	for folder in folders:
		log.info(f"Trying to load hashes for {folder}")
		files = try_load_hashes(base, folder)
		if files is None:
			log.info(f"Failed to load hashes for {folder}, scanning")
			scan_save_hashes(base, folder)
			files = try_load_hashes(base, folder)
		log.info(f"Finished loading hashes for {folder}. {len(files)} hashes loaded")
		all_files_by_folder[folder] = files

		for file in files:
			files_by_hash[file.file_hash].append(file)
			files_by_name[file.name].append(file)
			files_by_with_parent[file.with_parent].append(file)
			files_by_path[file.path].append(file)
	sys.exit()

	matched_hashes, total_hashes = 0, 0
	files_with_no_hash_matches = []
	files_with_no_hash_name_matches = []
	files_with_no_hash_with_parent_matches = []
	files_with_no_hash_but_with_name_matches = []

	files_with_exact_matches = defaultdict(int)
	folder = "xyz_1"
	log.info(f"Iterating {len(all_files_by_folder[folder]):,} files in folder {folder}")
	for file in all_files_by_folder[folder]:
		matched_by_hash = lookup_exclude(files_by_hash, file, "file_hash")
		matched_by_name = lookup_exclude(files_by_name, file, "name")
		matched_by_with_parent = lookup_exclude(files_by_with_parent, file, "with_parent")
		matched_by_path = lookup_exclude(files_by_path, file, "path")
		if matched_by_path is not None:
			exact_matches = 0
			for matched_file in matched_by_path:
				if matched_file.file_hash == file.file_hash:
					exact_matches += 1
			files_with_exact_matches[exact_matches] += 1

		if matched_by_hash is None:
			files_with_no_hash_matches.append(file)
			if matched_by_name is None:
				files_with_no_hash_name_matches.append(file)
			else:
				files_with_no_hash_but_with_name_matches.append(file)
			if matched_by_with_parent is None:
				files_with_no_hash_with_parent_matches.append(file)
		else:
			matched_hashes += 1
		total_hashes += 1
		if total_hashes % 10000 == 0:
			log.info(f"{total_hashes:,}/{len(all_files_by_folder[folder]):,}")

	log.info(f"{folder}: {matched_hashes} matched, {total_hashes} total")
	log.info(f"{folder}: Files with no hash matches: {len(files_with_no_hash_matches)}")
	for file in files_with_no_hash_matches[:10]:
		log.info(f"    {file}")
	log.info(f"{folder}: Files with no hash matches and no name matches: {len(files_with_no_hash_name_matches)}")
	for file in files_with_no_hash_name_matches[:10]:
		log.info(f"    {file}")
	log.info(f"{folder}: Files with no hash matches but with name matches: {len(files_with_no_hash_but_with_name_matches)}")
	for file in files_with_no_hash_but_with_name_matches[:10]:
		log.info(f"    {file}")
	log.info(f"{folder}: Files with no hash matches and no parent matches: {len(files_with_no_hash_with_parent_matches)}")
	for file in files_with_no_hash_with_parent_matches[:10]:
		log.info(f"    {file}")
	for matches, count in files_with_exact_matches.items():
		log.info(f"{count} files have {matches} exact matches")

	# for folder in all_folders.keys():
	# 	matched_hashes, total_hashes = 0, 0
	# 	for folder2, path, file_hash, file_type in all_folders[folder]:
	# 		if len(all_files[file_hash]) > 1:
	# 			matched_hashes += 1
	# 		total_hashes += 1
	# 	log.info(f"{folder}: {matched_hashes} matched, {total_hashes} total")


