import requests

prod_base = "https://api.pushshift.io/reddit/comment/search"# "limit", "before"
beta_base = "https://beta.pushshift.io/search/reddit/comments"# "size", "max_created_utc"

query = "remindme"

response = requests.get(f"{prod_base}?q={query}&limit=100", headers={'User-Agent': "watchful1 test agent"}, timeout=10)
data = response.json()['data']

prod_ids = set()
for comment in data:
	prod_ids.add(comment['id'])

print(f"Prod returned {len(prod_ids)} comments")

beta_url = f"{beta_base}?id={','.join(prod_ids)}"

response = requests.get(f"{prod_base}?q={query}&limit=100", headers={'User-Agent': "watchful1 test agent"}, timeout=10)
data = response.json()['data']

for comment in data:
	if comment['id'] not in prod_ids:
		print(f"{comment['id']} missing")
