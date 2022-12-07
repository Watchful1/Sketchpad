import praw
import prawcore
import discord_logging
import traceback
import time

log = discord_logging.init_logging(debug=True)

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful12")

	subreddits = []
	with open("quaran_subs.txt", 'r') as handle:
		for line in handle.readlines():
			subreddits.append(line.strip())

	log.info(f"Checking {len(subreddits)} subreddits")

	quarantined_handle = open("quarantined_confirmed.txt", 'w')

	success = 0
	forbidden = 0
	notfound = 0
	redirect = 0
	count_processed = 0
	for subreddit_name in subreddits:
		count_processed += 1
		try:
			reddit.subreddit(subreddit_name)._fetch()
			success += 1
			log.debug(f"{count_processed}/{len(subreddits)}: Success: https://www.reddit.com/r/{subreddit_name}")
		except prawcore.exceptions.Forbidden:
			# quarantined or private
			forbidden += 1
			log.debug(f"{count_processed}/{len(subreddits)}: Forbidden: https://www.reddit.com/r/{subreddit_name}")
			quarantined_handle.write(f"https://www.reddit.com/r/{subreddit_name}\n")
			quarantined_handle.flush()
		except prawcore.exceptions.NotFound:
			# banned
			notfound += 1
			log.debug(f"{count_processed}/{len(subreddits)}: NotFound: https://www.reddit.com/r/{subreddit_name}")
		except prawcore.exceptions.Redirect:
			# never existed
			redirect += 1
			log.debug(f"{count_processed}/{len(subreddits)}: Redirect: https://www.reddit.com/r/{subreddit_name}")
		except Exception as err:
			log.info(f"Error {err}: https://www.reddit.com/r/{subreddit_name}")
			log.info(traceback.format_exc())
			break
		log.info(f"{count_processed}/{len(subreddits)} : {success}/{forbidden}/{notfound}/{redirect}")

	quarantined_handle.close()

