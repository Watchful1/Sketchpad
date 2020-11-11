import praw

# deleted comment
# removed comment
# deleted self post
# removed self post
# deleted link post
# removed link post
# deleted image post
# removed image post

# view each as author, mod, unaffiliated

subreddit_name = "SubTestBot1"

reddit_mod = praw.Reddit("Watchful1")
reddit_author = praw.Reddit("Watchful1BotTest")
reddit_other = praw.Reddit("Watchful1Bot")

# make a self post

reddit_author.subreddit(subreddit_name).submit()
