import praw
from urllib.parse import urljoin
from praw.models import base
from praw.models import ListingGenerator, ModmailConversation
from datetime import datetime

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1")

	# path = "api/mod/conversations/search?q=ylee186"
	# params = {"origin":"https://mod.reddit.com"}
	# #params["raw_json"] = 1
	# url = urljoin(reddit._core._requestor.oauth_url, path)
	# response = reddit._core._request_with_retries(
	# 	data=None,
	# 	files=None,
	# 	json=None,
	# 	method="GET",
	# 	params=params,
	# 	timeout=reddit.config.timeout,
	# 	url=url,
	# )

	# response = reddit._core.request(
	# 	"GET",
	# 	"api/mod/conversations/search?q=ylee186",
	# 	timeout=reddit.config.timeout,
	# )

	response = reddit.get("api/mod/conversations/search?q=ylee186")

	# params = {}
	# base.PRAWBase._safely_add_arguments(
	# 	params,
	# 	"params",
	# 	sort=None,
	# 	state=None,
	# 	#q="ylee186"
	# )
	#
	# response = reddit.get("api/mod/conversations")
	# for conversation_id in response["conversationIds"]:
	# 	data = {
	# 		"conversation": response["conversations"][conversation_id],
	# 		"messages": response["messages"],
	# 	}
	# 	conversation = ModmailConversation.parse(
	# 		data, reddit, convert_objects=False
	# 	)
	# 	print(f"{conversation.id}:{conversation.owner.display_name}:{conversation.authors[0].name}")

	print("done")
