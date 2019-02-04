import json
import time
import bisect
import os
import sys
from collections import defaultdict

# with open(file, 'rb') as handle:
# 	decomp = lzma.LZMADecompressor(lzma.FORMAT_XZ)
# 	while not decomp.eof:
# 		comp_data = handle.read(32000)
# 		uncomp_data = decomp.decompress(comp_data)
# 		string_data = uncomp_data.decode('utf-8')
# 		print(string_data)

# Alternate method to stream the decompression to handle extremely large files
# with open("filename.zst", 'rb') as fh:
#     dctx = zstd.ZstdDecompressor()
#     with dctx.stream_reader(fh) as reader:
#         previous_line = ""
#         while True:
#             chunk = reader.read(65536)
#             if not chunk:
#                 break
#
#             string_data = chunk.decode('utf-8')
#             lines = string_data.split("\n")
#             for i, line in enumerate(lines[:-1]):
#                 if i == 0:
#                     line = previous_line + line
#                 object = json.loads(line)
#             previous_line = lines[-1]

folder = r"D:\reddit\submissions"
numFiles = 0
totalSize = 0
paths = []
for jsonFile in os.listdir(folder):
	if jsonFile.endswith(".xz") or jsonFile.endswith(".bz2"):
		continue
	numFiles += 1
	path = folder+"\\"+jsonFile
	paths.append(path)
	totalSize += os.path.getsize(path)

totalSizeInMb = "{:,}".format(int(totalSize/1000000))
print(f"Parsing {numFiles} files of total size {totalSizeInMb} mb")

for path in paths:
	with open(path, 'r') as f:
		print(f"Parsing: {path}")
		currentSubmissions = 0
		for submissionLine in f:
			currentSubmissions += 1

			submission = json.loads(submissionLine)
			if submission['id'] == '6vxtw7':
				print(str(submission))
sys.exit()

totalSeconds = 0
totalBytesParsed = 0
totalFilesParsed = 0
totalFileSubmissions = 0
submissionsPerByte = 1

trimmedWords = 0

totalSubmissions = 0
allWords = defaultdict(int)
startTime = time.perf_counter()
for path in paths:
	with open(path, 'r') as f:
		print(f"Parsing: {path}")
		currentSubmissions = 0
		totalFilesParsed += 1
		currentFileSize = os.path.getsize(path)
		for submissionLine in f:
			totalSubmissions += 1
			currentSubmissions += 1

			submission = json.loads(submissionLine)
			words = submission['title'].lower().split(" ")
			for word in words:
				allWords[word] += 1

			if currentSubmissions % 10000 == 0:
				seconds = int(time.perf_counter() - startTime)
				speed = int(totalSubmissions / max(seconds, 1))
				if totalBytesParsed == 0:
					print(f"File {totalFilesParsed}/{numFiles}, submissions, {currentSubmissions}, per second {speed}")
				else:
					submissionsInFile = int(currentFileSize * submissionsPerByte)
					submissionsLeftFile = submissionsInFile - currentSubmissions
					secondsLeftFile = int(submissionsLeftFile / speed)
					submissionsTotal = int(totalSize * submissionsPerByte)
					submissionsLeftTotal = submissionsTotal - totalSubmissions
					secondsLeftTotal = int(submissionsLeftTotal / speed)

					print(f"File {totalFilesParsed}/{numFiles}, submissions, {currentSubmissions}, per second {speed}. Left file {secondsLeftFile}, total {secondsLeftTotal}")

			# if currentSubmissions % 100000 == 0:
			# 	break

		totalBytesParsed += currentFileSize
		totalFileSubmissions += currentSubmissions
		submissionsPerByte = totalFileSubmissions / totalBytesParsed

		# trim allWords so we don't run out of memory. Doing this means there's a small chance we lose words
		# that might otherwise appear in higher numbers in other months, but I think it's unlikely
		beforeAllSize = len(allWords)
		for key in list(allWords.keys()):
			if allWords[key] < 1000:
				trimmedWords += allWords[key]
				del allWords[key]
		print(f"Allwords trimmed from {beforeAllSize} to {len(allWords)}")


print(f"{totalSubmissions} total submissions in {int(time.perf_counter() - startTime)} seconds")

print(f"Found {len(allWords) + trimmedWords} words")

stopWords = set()
f = open('stopwords.txt', 'r')
for word in f:
	stopWords.add(word.strip())
print(f"Excluding {len(stopWords)}")
f.close()

wordsCountSorted = []
limit = 1000  # let's only look at words that occur at least a thousand times to make sorting easier
for word in allWords:
	if allWords[word] > limit:
		if word not in stopWords:
			bisect.insort(wordsCountSorted, (allWords[word], word))

print(f"Words over 1000: {len(wordsCountSorted)}")
# print out the top 1000 items
count = 0
for wordTuple in wordsCountSorted[::-1]:
	count += 1
	print(str(wordTuple[0]) + " : " + str(wordTuple[1]))
	if count > 1000:
		break
