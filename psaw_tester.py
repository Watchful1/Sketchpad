from psaw import PushshiftAPI
api = PushshiftAPI()

submissions = []
for submission in api.search_submissions(subreddit="askreddit", limit=2000):
	submissions.append(submission)

print(len(list(submissions)))
