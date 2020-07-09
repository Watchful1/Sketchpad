import praw
from praw.models import MoreComments

# example to load only top level comments of a large thread
# this copies most of its logic from the praw code here https://github.com/praw-dev/praw/blob/master/praw/models/comment_forest.py
# https://www.reddit.com/r/AskReddit/comments/hl30ln/what_hobby_does_not_get_more_expensive_the_more/


# go through the comment tree and find all the top level MoreComments objects
# if we're doing this right, there should only ever be one. Since we throw away any MoreComments objects that aren't top level
# also print out how many comments there are so we know how we're doing
def gather_more_comments(submission):
	top_level_comment_count = 0
	more_comments = []
	for top_level_comment in submission.comments:
		if isinstance(top_level_comment, MoreComments):
			more_comments.append(top_level_comment)
		else:
			top_level_comment_count += 1

	print(f"Comments: {top_level_comment_count}, MoreComments objects: {len(more_comments)}")
	return more_comments


thread_id = "hl30ln"
reddit = praw.Reddit("Watchful1BotTest")

submission = reddit.submission(thread_id)
# count the number of API requests we've made
count_requests = 1

# get the initial MoreComments list
more_comments = gather_more_comments(submission)
# loop until the list is empty, ie, there are no top level MoreComments objects left
while more_comments:
	# grab the first one, just in case there's more than one for some reason
	more_comment = more_comments.pop()

	# call the fetch method to get all the comments from the API
	new_comments = more_comment.comments(update=False)

	count_requests += 1

	# insert all new comments into the tree
	for comment in new_comments:
		# if it's a MoreComments object, but the parent isn't the submission, then it belongs somewhere else in the tree
		# normally PRAW just throws it at the bottom anyway, since it will fetch all the comments and then figure out
		# where they go. We don't want to fetch these child comments, so we throw this away
		if isinstance(comment, MoreComments) and comment.parent_id.startswith('t1_'):
			continue
		submission.comments._insert_comment(comment)

	# remove this MoreComments item from the tree
	submission.comments._comments.remove(more_comment)

	# iterate through the top level tree again to find the new MoreComments object
	more_comments = gather_more_comments(submission)

print(f"Done in {count_requests} requests")
