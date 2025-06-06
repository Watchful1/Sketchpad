import praw


input_file_name = "ids.txt"
output_file_name = "comments.txt"
if __name__ == "__main__":
	reddit = praw.Reddit("Watchful12")

	ids = []
	with open(input_file_name, 'r') as txt:
		for line in txt:
			ids.append(f"t1_{line.strip()}")
	print(f"Loaded ids: {len(ids):,}")

	count = 0
	with open(output_file_name, 'w') as txt:
		for comment in reddit.info(ids):
			if comment.author is not None:
				txt.write(f"{comment.id}	{comment.author.name}	{comment.score}\n")
			count += 1
			if count % 1000 == 0:
				print(f"{count:,}/{len(ids):,}")

	print(f"{count:,}/{len(ids):,}")
