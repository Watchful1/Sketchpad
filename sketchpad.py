from psaw import PushshiftAPI
import datetime as dt

api = PushshiftAPI()
for submission in api.search_submissions(subreddit='pushshift', limit=500, sort='desc', sort_type='created_utc'):
    print(submission.title)
    time = submission.created_utc
    print(dt.datetime.fromtimestamp(time))
