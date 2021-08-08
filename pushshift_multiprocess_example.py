import zstandard
import os
import json
import sys
import time
from datetime import datetime
import logging.handlers
import multiprocessing


# sets up logging to the console as well as a file
log = logging.getLogger("bot")
log.setLevel(logging.DEBUG)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')

log_stderr_handler = logging.StreamHandler()
log_stderr_handler.setFormatter(log_formatter)
log.addHandler(log_stderr_handler)
if not os.path.exists("logs"):
	os.makedirs("logs")
log_file_handler = logging.handlers.RotatingFileHandler(
	os.path.join("logs", "bot.log"), maxBytes=1024*1024*16, backupCount=5)
log_file_handler.setFormatter(log_formatter)
log.addHandler(log_file_handler)


# this script iterates through zst compressed ndjson files, like the pushshift reddit dumps, loads each line
# and passes it into the save_obj function, if it function returns true for a line, it's written out into a
# separate file for that month. After all the ndjson files are processed, it iterates through the resulting
# files and combines them into a final file.

# once complete, the combined file can easily be processed like
# with open(file_path, 'r') as file:
#     for line in file:
#         obj = json.loads(line)

# features:
#    - multiple processes in parallel to maximize drive read and decompression
#    - saves state as it completes each file and picks up where it stopped
#    - detailed progress indicators


# number of parallel processes to use
COUNT_PROCESSES = 10
# full path to input folder
INPUT_FOLDER = ""
# full path to output folder
OUTPUT_FOLDER = ""
# name of output and working folders, used to distinguish separate runs
OUTPUT_FILE_NAME = ""


# takes in a single line object and returns true if it should be saved
def save_obj(obj):
	return obj['subreddit'] == "redditdev"


# convenience object used to pass status information between processes
class FileConfig:
	def __init__(self, input_path, output_path=None, complete=False, lines_processed=0):
		self.input_path = input_path
		self.output_path = output_path
		self.file_size = os.stat(input_path).st_size
		self.complete = complete
		self.bytes_processed = self.file_size if complete else 0
		self.lines_processed = lines_processed if complete else 0


# used for calculating running average of read speed
class Queue:
	def __init__(self, max_size):
		self.list = []
		self.max_size = max_size

	def put(self, item):
		if len(self.list) >= self.max_size:
			self.list.pop(0)
		self.list.append(item)

	def peek(self):
		return self.list[0] if len(self.list) > 0 else None


# builds file paths
def folder_helper(output_folder, output_file_name):
	working_folder = os.path.join(output_folder, "pushshift_working_dir_" + output_file_name)
	status_file = os.path.join(working_folder, output_file_name + ".json")
	return working_folder, status_file


# save file information and progress to a json file
# we don't want to save the whole FileConfig object, since some of the info resets if we restart
def save_file_list(input_files, output_folder, output_file_name):
	working_folder, status_json_file_name = folder_helper(output_folder, output_file_name)
	if not os.path.exists(working_folder):
		os.makedirs(working_folder)
	simple_file_list = []
	for file in input_files:
		simple_file_list.append([file.input_path, file.output_path, file.complete, file.lines_processed])
	with open(status_json_file_name, 'w') as status_json_file:
		status_json_file.write(json.dumps(simple_file_list, indent=4))


# load file information from the json file and recalculate file sizes
def load_file_list(output_folder, output_file_name):
	_, status_json_file_name = folder_helper(output_folder, output_file_name)
	if os.path.exists(status_json_file_name):
		with open(status_json_file_name, 'r') as status_json_file:
			simple_file_list = json.load(status_json_file)
			input_files = []
			for simple_file in simple_file_list:
				input_files.append(
					FileConfig(simple_file[0], simple_file[1], simple_file[2], simple_file[3])
				)
			return input_files
	else:
		return None


# open a zst compressed ndjson file and yield lines one at a time
# also passes back file progress
def read_lines_zst(file_name):
	with open(file_name, 'rb') as file_handle:
		buffer = ''
		reader = zstandard.ZstdDecompressor(max_window_size=2**28).stream_reader(file_handle)
		while True:
			chunk = reader.read(2**24).decode()  # read a 16mb chunk at a time. There are some really big comments
			if not chunk:
				break
			lines = (buffer + chunk).split("\n")

			for line in lines[:-1]:
				yield line, file_handle.tell()

			buffer = lines[-1]
		reader.close()


# base of each separate process. Loads a file, iterates through lines and writes out
# the ones where save_obj() returns true. Also passes status information back to the parent via a queue
def process_file(file, working_folder, queue):
	output_file = None
	for line, file_bytes_processed in read_lines_zst(file.input_path):
		obj = json.loads(line)
		if save_obj(obj):
			if output_file is None:
				if file.output_path is None:
					created = datetime.utcfromtimestamp(int(obj['created_utc']))
					file.output_path = os.path.join(working_folder, created.strftime("%Y-%m"))
				output_file = open(file.output_path, 'w')
			output_file.write(line)
			output_file.write("\n")
		file.lines_processed += 1
		if file.lines_processed % 100000 == 0:
			file.bytes_processed = file_bytes_processed
			queue.put(file)

	if output_file is not None:
		output_file.close()

	file.complete = True
	file.bytes_processed = file.file_size
	queue.put(file)


if __name__ == '__main__':
	# overwrite the config variables with passed in arguments
	input_folder = sys.argv[1] if INPUT_FOLDER == "" and len(sys.argv) >= 2 else INPUT_FOLDER
	assert input_folder is not None and input_folder != ""
	output_folder = sys.argv[2] if OUTPUT_FOLDER == "" and len(sys.argv) >= 3 else OUTPUT_FOLDER
	assert output_folder is not None and output_folder != ""
	output_file_name = sys.argv[3] if OUTPUT_FILE_NAME == "" and len(sys.argv) >= 4 else OUTPUT_FILE_NAME
	assert output_file_name is not None and output_file_name != ""

	log.info(f"Loading files from: {input_folder}")
	log.info(f"Writing output to: {(os.path.join(output_folder, output_file_name + '.txt'))}")

	multiprocessing.set_start_method('spawn')
	queue = multiprocessing.Manager().Queue()
	input_files = load_file_list(output_folder, output_file_name)
	working_folder, _ = folder_helper(output_folder, output_file_name)
	# if the file list wasn't loaded from the json, this is the first run, find what files we need to process
	if input_files is None:
		input_files = []
		for subdir, dirs, files in os.walk(input_folder):
			for file_name in files:
				if file_name.endswith(".zst"):
					input_path = os.path.join(subdir, file_name)
					input_files.append(FileConfig(input_path))

		save_file_list(input_files, output_folder, output_file_name)

	files_processed = 0
	total_bytes = 0
	total_bytes_processed = 0
	total_lines_processed = 0
	files_to_process = []
	# calculate the total file size for progress reports, build a list of incomplete files to process
	for file in input_files:
		total_bytes += file.file_size
		if file.complete:
			files_processed += 1
			total_lines_processed += file.lines_processed
			total_bytes_processed += file.file_size
		else:
			files_to_process.append(file)

	log.info(f"Processed {files_processed} of {len(input_files)} files with {(total_bytes_processed / (2**30)):.2f} of {(total_bytes / (2**30)):.2f} gigabytes")

	start_time = time.time()
	if len(files_to_process):
		progress_queue = Queue(100)
		progress_queue.put([start_time, total_lines_processed, total_bytes_processed])
		speed_queue = Queue(20)
		# start the workers
		with multiprocessing.Pool(processes=COUNT_PROCESSES) as pool:
			workers = pool.starmap_async(process_file, [(file, working_folder, queue) for file in files_to_process], error_callback=log.info)
			while not workers.ready():
				# loop until the workers are all done, pulling in status messages as they are sent
				file_update = queue.get()
				# I'm going to assume that the list of files is short enough that it's no
				# big deal to just iterate each time since that saves a bunch of work
				total_lines_processed = 0
				total_bytes_processed = 0
				files_processed = 0
				i = 0
				for file in input_files:
					if file.input_path == file_update.input_path:
						input_files[i] = file_update
						file = file_update
					total_lines_processed += file.lines_processed
					total_bytes_processed += file.bytes_processed
					files_processed += 1 if file.complete else 0
					i += 1
				if file_update.complete:
					save_file_list(input_files, output_folder, output_file_name)
				current_time = time.time()
				progress_queue.put([current_time, total_lines_processed, total_bytes_processed])

				first_time, first_lines, first_bytes = progress_queue.peek()
				bytes_per_second = int((total_bytes_processed - first_bytes)/(current_time - first_time))
				speed_queue.put(bytes_per_second)
				seconds_left = int((total_bytes - total_bytes_processed) / int(sum(speed_queue.list) / len(speed_queue.list)))
				minutes_left = int(seconds_left / 60)
				hours_left = int(minutes_left / 60)
				days_left = int(hours_left / 24)

				log.info(
					f"{total_lines_processed:,} lines at {(total_lines_processed - first_lines)/(current_time - first_time):,.0f}/s : "
					f"{(total_bytes_processed / (2**30)):.2f} gb at {(bytes_per_second / (2**20)):,.0f} mb/s, {(total_bytes_processed / total_bytes) * 100:.0f}% : "
					f"{files_processed}/{len(input_files)} files : "
					f"{(str(days_left) + 'd ' if days_left > 0 else '')}{hours_left - (days_left * 24)}:{minutes_left - (hours_left * 60)}:{seconds_left - (minutes_left * 60)} remaining")

	log.info(f"{total_lines_processed:,} : {(total_bytes_processed / (2**30)):.2f} gb, {(total_bytes_processed / total_bytes) * 100:.0f}% : {files_processed}/{len(input_files)}")

	working_file_paths = []
	# build a list of output files to combine
	for file in input_files:
		if file.output_path is not None:
			if not os.path.exists(file.output_path):
				log.info(f"Output file {file.output_path} doesn't exist")
			else:
				working_file_paths.append(file.output_path)

	log.info(f"Processing complete, combining {len(working_file_paths)} result files")

	output_lines = 0
	output_file_path = os.path.join(output_folder, output_file_name + ".txt")
	# combine all the output files into the final results file
	with open(output_file_path, 'w') as output_file:
		i = 0
		for working_file_path in working_file_paths:
			i += 1
			log.info(f"Reading {i}/{len(working_file_paths)}")
			with open(working_file_path, 'r') as input_file:
				for line in input_file.readlines():
					output_lines += 1
					output_file.write(line)

	log.info(f"Finished combining files, {output_lines} lines written to {output_file_path}")
