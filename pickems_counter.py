import discord_logging
import requests
from collections import defaultdict

log = discord_logging.init_logging(debug=True)

if __name__ == "__main__":
	urls = [
		"https://pickem.overwatchleague.com/api/leaderboards?slug=reddit-cow&season=2022&stage=kickoff-clash",
		"https://pickem.overwatchleague.com/api/leaderboards?slug=reddit-cow&season=2022&stage=midseason-madness",
		"https://pickem.overwatchleague.com/api/leaderboards?slug=reddit-cow&season=2022&stage=summer-showdown",
		"https://pickem.overwatchleague.com/api/leaderboards?slug=reddit-cow&season=2022&stage=countdown-playoffs",
	]

	users = defaultdict(int)
	for url in urls:
		for user in requests.get(url).json():
			if user['points'] is not None:
				users[user['username']] += int(user['points'])

	i = 0
	for user in sorted(users, key=users.get, reverse=True):
		log.info(f"{user}: {users[user]}")
		i += 1
		if i >= 7:
			break
