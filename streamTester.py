import praw
from collections import defaultdict

r = praw.Reddit("Watchful1BotTest")

seen = set()
items = defaultdict(list)
order = []
count = 0
duplicates = 0

for post in r.subreddit('all').stream.submissions(skip_existing=True):
	count += 1
	if count % 100 == 0:
		print(f"Searched: {count} : {duplicates}")
	if count >= 5000:
		break

	items[post.id].append(count)
	if post.id in seen:
		duplicates += 1
	else:
		order.append(post.id)
	seen.add(post.id)

print(f"Searched: {count} : {duplicates}")
with open("posts.txt", 'w') as txt:
	for item in order:
		txt.write(f"{item}/{len(items[item])}: [")
		txt.write(','.join(str(x) for x in items[item]))
		txt.write("]\n")
