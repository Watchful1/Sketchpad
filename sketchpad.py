import praw

reddit = praw.Reddit("Watchful1BotTest")

user = reddit.redditor("Watchful1")
submissions = user.submissions.new()

for post in submissions:
	subreddit = post.subreddit
	url = subreddit.url
	final = url.split("/")[-2].lower()
	print(final)
