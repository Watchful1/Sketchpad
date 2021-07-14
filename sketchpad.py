import praw
from datetime import datetime
import pandas as pd

pd.set_option("display.max_rows", None, "display.max_columns", None)
reddit = praw.Reddit("Watchful1BotTest")

submissions = []

reddit_sub = reddit.subreddit('CryptoCurrency')
keyword = "DAILY DISCUSSION"
resp = reddit_sub.search(keyword, limit=100)

for submission in resp:
    if submission.num_comments >= 100:
        date = datetime.utcfromtimestamp(submission.created_utc)
        submissions.append([submission.title, submission.score, submission.id,          submission.subreddit, submission.url, submission.num_comments, submission.created, date])

submissions = pd.DataFrame(submissions,columns=['title', 'score', 'id', 'subreddit', 'url', 'num_comments', 'created', 'date'])

submissions = submissions.sort_values(by='date')

for column in submissions:
    print(submissions[column])
#print(submissions)
