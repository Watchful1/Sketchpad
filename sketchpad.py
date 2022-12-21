import praw

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1")

	subreddit = reddit.subreddit("CompetitiveOverwatch")
	for report in subreddit.mod.reports("comments", limit=None):
		print(f"{report}")
