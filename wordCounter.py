import json
import time
import bisect

f = open('RS_2018-09', 'r')
totalSubmission = 13107215  # set manually after running once

counter = 0
wordsCount = {}
startTime = time.perf_counter()
for submissionLine in f:
	counter += 1

	submission = json.loads(submissionLine)
	words = submission['title'].lower().split(" ")
	for word in words:
		if word in wordsCount:
			wordsCount[word] += 1
		else:
			wordsCount[word] = 1

	if counter % 10000 == 0:
		seconds = int(time.perf_counter() - startTime)
		if seconds == 0:
			speed = 1
		else:
			speed = int(counter / seconds)
		secondsLeft = int((totalSubmission - counter) / speed)
		print(f"Submissions: {counter}, per second {speed}. Seconds left {secondsLeft}")

f.close()
print(f"{counter} total submissions in {int(time.perf_counter() - startTime)} seconds")

print(f"Found {len(wordsCount)} words")

wordsCountSorted = []
limit = 1000  # let's only look at words that occur at least a thousand times to make sorting easier
for word in wordsCount:
	if wordsCount[word] > limit:
		bisect.insort(wordsCountSorted, (wordsCount[word], word))

print(f"Words over 1000: {len(wordsCountSorted)}")
# print out the top 100 items
count = 0
for wordTuple in wordsCountSorted[::-1]:
	count += 1
	print(str(wordTuple[0]) + " : " + str(wordTuple[1]))
	if count > 100:
		break


