import praw
from datetime import datetime
import logging
import prawcore
import csv
import sys

log = logging.getLogger("bot")
log.setLevel(logging.INFO)
log_formatter = logging.Formatter('%(asctime)s - %(levelname)s: %(message)s')
log_handler = logging.StreamHandler()
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

if __name__ == "__main__":
	thread = "https://www.reddit.com/r/RandomThoughts/comments/1kwxrzn/no_filterjust_your_gut_reaction_gray_hair_what/"
	csv_file_name = "comments.csv"

	reddit = praw.Reddit("Watchful1")

	log.info(f"Checking thread")
	submission = reddit.submission(url=thread)
	try:
		log.info(f"Reddit reports the submission has {submission.num_comments} total comments")
	except prawcore.exceptions.NotFound:
		log.info(f"Submission not found, make sure your link works")
		sys.exit(1)

	log.info(f"Loading all comments from reddit. If there are lots, this might take a while. Up to an hour or more in extreme cases of hundreds of thousands of comments.")
	comments = submission.comments
	comments.replace_more(limit=None)
	comments_list = comments.list()

	log.info(f"Downloaded {len(comments_list)} comments. If this is less than the previous number, it's likely the mods removed some from the thread.")

	log.info(f"Writing comments to csv file {csv_file_name}")
	handle = open(csv_file_name, 'w', encoding='UTF-8', newline='')
	writer = csv.writer(handle)
	writer.writerow(['score','date_time','author','link','id','is_top_level','body'])
	for comment in comments_list:
		output_list = []
		output_list.append(comment.score)
		output_list.append(datetime.fromtimestamp(comment.created_utc).strftime("%Y-%m-%d"))
		output_list.append(f"u/{comment.author}")
		output_list.append(f"https://www.reddit.com{comment.permalink}")
		output_list.append(comment.id)
		output_list.append(comment.parent_id[0:2] == "t3")
		output_list.append(comment.body)
		writer.writerow(output_list)

	log.info(f"Finished")
	handle.close()
