import praw
from praw.models import MoreComments
from prawcore.exceptions import RequestException, ServerError

reddit = praw.Reddit("Watchful1BotTest")


def count_comments(comments):
    count_c, count_m = 0, 0
    for comment in comments:
        if isinstance(comment, MoreComments):
            count_m += 1
        else:
            count_c += 1
    print(f"comments: {count_c}, more: {count_m}")


submission = reddit.submission("i5l1m1")
count_comments(submission.comments.list())
while True:
    try:
        submission.comments.replace_more(limit=None)
        break
    except (RequestException, ServerError):
        print("Hit request exception, retrying")
        count_comments(submission.comments.list())
count_comments(submission.comments.list())
for comment in submission.comments.list():
    print(comment.body)
