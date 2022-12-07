import discord_logging
import praw

log = discord_logging.init_logging(debug=True)

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1")
	thread1 = reddit.submission("xl64vn")
	thread2 = reddit.submission("xm29lm")

	log.info("Loading thread 1")
	thread1.comments.replace_more(limit=None)
	log.info("Done")
	log.info("Loading thread 2")
	thread2.comments.replace_more(limit=None)
	log.info("Done")

	log.info("Building commenters for 1")
	thread1_commenters = set()
	for comment in thread1.comments.list():
		thread1_commenters.add(comment.author.name)
	log.info(f"Count commenters {len(thread1_commenters)}")

	log.info("Building commenters for 2")
	thread2_commenters = set()
	for comment in thread2.comments.list():
		thread2_commenters.add(comment.author.name)
	log.info(f"Count commenters {len(thread2_commenters)}")

	missing_commenters = []
	for commenter in thread1_commenters:
		if commenter not in thread2_commenters:
			missing_commenters.append(commenter)

	log.info(f"Missing commenters {len(missing_commenters)}")
	for commenter in missing_commenters:
		log.info(f"u/{commenter}")

