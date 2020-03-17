import zstandard
import lzma
import os
import json
import discord_logging
from datetime import datetime


log = discord_logging.init_logging()


def read_lines_zst(file_name):
	with open(file_name, 'rb') as file_handle:
		buffer = ''
		reader = zstandard.ZstdDecompressor().stream_reader(file_handle)
		while True:
			chunk = reader.read(16384).decode()
			if not chunk:
				break
			lines = (buffer + chunk).split("\n")

			for line in lines[:-1]:
				yield line

			buffer = lines[-1]


def read_lines_xz(file_name):
	with lzma.open(file_name, mode='rt') as file_handle:
		for line in file_handle:
			yield line


input_folder = r'D:\reddit\comments'
input_file = 'RC_2015-10'

input_path = os.path.join(input_folder, input_file)

xz_lines = 0
for line in read_lines_xz(input_path + ".xz"):
	obj = json.loads(line)
	created = datetime.utcfromtimestamp(int(obj['created_utc']))

	xz_lines += 1

	if xz_lines % 100000 == 0:
		log.info(created.strftime("XZ: %Y-%m-%d %H:%M:%S"))

log.info(f"XZ Lines: {xz_lines}")

zst_lines = 0
for line in read_lines_zst(input_path + ".zst"):
	obj = json.loads(line)
	created = datetime.utcfromtimestamp(int(obj['created_utc']))

	zst_lines += 1

	if zst_lines % 100000 == 0:
		log.info(created.strftime("ZST: %Y-%m-%d %H:%M:%S"))

log.info(f"ZST Lines: {zst_lines}")

log.info(f"ZX: {xz_lines} ZST: {zst_lines}")
if xz_lines == zst_lines:
	log.info("Equal")
else:
	log.info("Not equal")
