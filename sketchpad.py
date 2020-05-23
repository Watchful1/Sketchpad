import praw

reddit = praw.Reddit("Watchful1BotTest")

reddit.subreddit('all').search("https://google.com")
