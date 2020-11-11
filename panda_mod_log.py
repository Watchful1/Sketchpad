import praw
import pandas as pd

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1")
	subreddit_name = "CompetitiveOverwatch"

	results = []
	for log in reddit.subreddit(subreddit_name).mod.log(limit=None):
		log_item = [log.subreddit, log.description, log.target_body, log.mod_id36, log.created_utc,
				   log.target_title, log.target_permalink, log.details, log.action, str(log.target_fullname)[0:6],
				   log.id, log.mod]
		results.append(log_item)
	logs_dataframe = pd.DataFrame(results, columns=['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
											  'target_title', 'target_permalink', 'details', 'action', 'target_author',
											  'id', '_mod'])

	logs_dataframe = logs_dataframe[['subreddit', 'description', 'target_body', 'mod_id36', 'created_utc',
								   'target_title', 'target_permalink', 'details', 'action', 'target_author',
								   'id', '_mod']]
	logs_dataframe.drop_duplicates(subset=['id'], inplace=True)
	logs_dataframe.to_csv(subreddit_name + '.csv', index=False)
