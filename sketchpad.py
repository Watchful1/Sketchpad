import praw

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1")

	subreddit = reddit.subreddit("CompetitiveOverwatch")
	for flair in subreddit.flair(redditor="Watchful1"):
		print(f"{flair['user'].name} : {flair['flair_text']}")
