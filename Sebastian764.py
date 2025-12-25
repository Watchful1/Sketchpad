import praw
import json
import time
from datetime import datetime

subreddit_list = [
	'medicine', 'nursing', 'Residency', 'medicalschool', 'pharmacy',
	'Dentistry',
	'Veterinary', 'ems', 'NewToEMS', 'medlabprofessionals', 'physicaltherapy',
	'radiology', 'slp', 'optometry', 'Chiropractic', 'therapists', 'socialwork',
	'psychotherapy', 'doctorsUK', 'cscareerquestions', 'sysadmin', 'devops',
	'ITCareerQuestions', 'webdev', 'softwareengineering', 'networking',
	'cybersecurity', 'datascience', 'gamedev', 'ProgrammerHumor',
	'qualityassurance', 'UI_Design', 'userexperience', 'skilledtrades',
	'Construction', 'Electricians', 'Plumbing', 'HVAC', 'Welding', 'Truckers',
	'Carpentry', 'Machinists', 'Lineman', 'Locksmith', 'millwrights',
	'oilandgasworkers', 'railroading', 'landscaping', 'Justrolledintotheshop',
	'engineering', 'civilengineering', 'mechanicalengineering',
	'electricalengineering', 'ChemicalEngineering', 'aerospace', 'biotech',
	'PLC',
	'Accounting', 'FinancialCareers', 'consulting', 'marketing', 'sales',
	'humanresources', 'supplychain', 'actuary', 'InsurancePros', 'realtors',
	'CommercialRealEstate', 'Lawyers', 'LawSchool', 'paralegal',
	'PublicDefenders',
	'KitchenConfidential', 'Chefit', 'TalesFromRetail', 'Serverlife',
	'bartenders',
	'flightattendants', 'TalesFromTheFrontDesk', 'starbucks', 'Custodians',
	'Teachers', 'Professors', 'highereducation', 'librarians', 'ece',
	'teaching',
	'graphic_design', 'filmmakers', 'editors', 'journalism', 'copywriting',
	'advertising', 'architecture', 'photography', 'videography', 'museumpros',
	'Firefighting', 'police', 'ProtectAndServe', 'securityguards',
	'911dispatchers',
	'jobs', 'careerguidance', 'resumes', 'recruitinghell', 'remotejobs',
	'civilservice', 'usajobs', 'nonprofit', 'csMajors', 'leetcode'
]

# Authenticate to Reddit
reddit = praw.Reddit("Watchful1BotTest",
					 user_agent='MacOS:RedditDataAnalyzer:v1.0 (by /u/Sebastian764)')

def comment_to_dict(comment):
	"""Convert a Reddit comment to a dictionary."""
	body = comment.body.strip() if comment.body else ''

	# Skip deleted comments
	if body == '[deleted]' or body == '[removed]':
		return None

	return {
		'id': comment.id,
		'author': str(comment.author) if comment.author else '[deleted]',
		'score': comment.score,
		'created_utc': comment.created_utc,
		'created_date': datetime.fromtimestamp(comment.created_utc).isoformat(),
		'body': body,
		'body_word_count': len(body.split()) if body else 0,
	}


def fetch_top_comments(post, top_percentage=0.5):
	"""Fetch top comments for a post, returning top 50% by upvote count."""
	try:
		post.comments.replace_more(limit=0)  # Load all top-level comments

		# Get all top-level comments and convert to dict (excluding deleted)
		all_comments = []
		for comment in post.comments:
			comment_dict = comment_to_dict(comment)
			if comment_dict:  # Only add if not deleted
				all_comments.append(comment_dict)

		if not all_comments:
			return []

		# Sort by score descending
		all_comments.sort(key=lambda x: x['score'], reverse=True)

		# Get top 50%
		top_count = max(1, int(len(all_comments) * top_percentage))
		return all_comments[:top_count]

	except Exception as e:
		print(f"    Error fetching comments for post {post.id}: {e}")
		return []


def post_to_dict(post, include_comments=True):
	"""Convert a Reddit post to a dictionary."""
	body = post.selftext.strip() if post.selftext else ''

	# Check if body is deleted
	if body == '[deleted]' or body == '[removed]':
		body = ''

	post_dict = {
		'id': post.id,
		'title': post.title,
		'score': post.score,
		'url': post.url,
		'permalink': f"https://reddit.com{post.permalink}",
		'created_utc': post.created_utc,
		'created_date': datetime.fromtimestamp(post.created_utc).isoformat(),
		'author': str(post.author) if post.author else '[deleted]',
		'num_comments': post.num_comments,
		'body': body,
		'body_word_count': len(body.split()) if body else 0,
		'is_self': post.is_self,
		'link_flair_text': post.link_flair_text,
		'upvote_ratio': post.upvote_ratio,
	}

	if include_comments:
		post_dict['top_comments'] = fetch_top_comments(post)
		post_dict['top_comments_count'] = len(post_dict['top_comments'])

	return post_dict


def fetch_top_posts(subreddit_name, time_filter, limit=1500):
	"""Fetch top posts from a subreddit with the given time filter."""
	subreddit = reddit.subreddit(subreddit_name)
	posts = []

	print(
		f"  Fetching top {limit} posts ({time_filter}) from r/{subreddit_name}...")

	try:
		for post in subreddit.top(time_filter=time_filter, limit=limit):
			posts.append(post_to_dict(post, include_comments=True))

			# Progress indicator every 100 posts
			if len(posts) % 100 == 0:
				print(f"    Fetched {len(posts)} posts...")

			# Small delay to respect rate limits
			time.sleep(0.5)
	except Exception as e:
		print(f"  Error fetching posts: {e}")

	print(f"  Completed: {len(posts)} posts fetched")
	return posts


def extract_subreddit_data(subreddit_name):
	"""Extract top posts of the year and all time for a subreddit."""
	print(f"\nProcessing r/{subreddit_name}...")

	# Fetch top posts of the year
	year_posts = fetch_top_posts(subreddit_name, 'year', limit=1500)
	year_post_ids = {post['id'] for post in year_posts}

	# Fetch top posts of all time
	all_time_posts_raw = fetch_top_posts(subreddit_name, 'all', limit=1500)

	# Remove duplicates: keep posts only in "all time" if they're not in "year"
	all_time_posts = [post for post in all_time_posts_raw if
					  post['id'] not in year_post_ids]

	print(
		f"  Deduplication: {len(all_time_posts_raw)} all-time posts -> {len(all_time_posts)} unique (removed {len(all_time_posts_raw) - len(all_time_posts)} duplicates)")

	return {
		'subreddit': subreddit_name,
		'extraction_date': datetime.now().isoformat(),
		'top_posts_year': {
			'time_filter': 'year',
			'count': len(year_posts),
			'posts': year_posts
		},
		'top_posts_all_time': {
			'time_filter': 'all',
			'count': len(all_time_posts),
			'note': 'Excludes posts already in top_posts_year to avoid duplicates',
			'posts': all_time_posts
		}
	}


def extract_all_subreddits(subreddit_list, output_file='reddit_top_posts.json'):
	"""Extract data from all subreddits and save to a single JSON file."""
	print(f"Starting extraction for {len(subreddit_list)} subreddits...")

	user = reddit.user.me()
	print(f"Authenticated as: {user}")

	data = {
		'metadata': {
			'extraction_date': datetime.now().isoformat(),
			'subreddits_count': len(subreddit_list),
			'posts_per_category': 1500,
			'note': 'Posts in top_posts_year are excluded from top_posts_all_time to avoid duplicates'
		},
		'subreddits': {}
	}

	for subreddit_name in subreddit_list:
		try:
			subreddit_data = extract_subreddit_data(subreddit_name)
			data['subreddits'][subreddit_name] = subreddit_data
		except Exception as e:
			print(f"Error processing r/{subreddit_name}: {e}")
			data['subreddits'][subreddit_name] = {
				'error': str(e),
				'subreddit': subreddit_name
			}

	# Save to JSON file
	print(f"\nSaving data to {output_file}...")
	with open(output_file, 'w', encoding='utf-8') as f:
		json.dump(data, f, indent=2, ensure_ascii=False)

	print(f"Done! Data saved to {output_file}")

	# Print summary
	print("\n=== Summary ===")
	for sub_name, sub_data in data['subreddits'].items():
		if 'error' not in sub_data:
			year_count = sub_data['top_posts_year']['count']
			all_time_count = sub_data['top_posts_all_time']['count']
			print(
				f"r/{sub_name}: {year_count} year posts, {all_time_count} all-time posts (unique)")

	return data


if __name__ == '__main__':
	# print(len(subreddit_list))
	test_list = subreddit_list  # [:2]
	extract_all_subreddits(test_list, output_file='reddit_top_posts.json')

# JSON output structure:
# {
#   "metadata": { "extraction_date": "...", "subreddits_count": 2, ... },
#   "subreddits": {
#     "example": {
#       "top_posts_year": {
#         "count": 1500,
#         "posts": [
#           {
#             "id": "...",
#             "title": "...",
#             "score": 1234,
#             "body": "post content here",
#             "body_word_count": 50,
#             "top_comments": [
#               { "id": "...", "author": "...", "score": 500, "body": "comment text", ... }
#             ],
#             "top_comments_count": 10,
#             ...
#           }
#         ]
#       },
#       "top_posts_all_time": { "count": X, "posts": [...] }
#     },
#     "example2": { ... }
#   }
# }