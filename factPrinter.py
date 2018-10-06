import praw
import config
import time
import os
import requests
import re
import traceback

from datetime import datetime

startTime = datetime.utcnow()

list_of_names = ["phylogenizer", "merlyn923", "unknown_name", "lego_c3po", "thechuck42", "circemoon", "_communist",
                 "dyleo", "themadflyentist", "millmoss", "so_then_i_said"]
sig = "*I am a bot created by /u/Phylogenizer and SEB. You can find more information " \
      "[here](https://www.reddit.com/r/whatsthissnake/comments/9db7am/introducing_phylobot_v02/) and report problems " \
      "[here](https://www.reddit.com/message/compose/?to=Phylogenizer).*"

commands = [
	{'command': "deadsnake", 'text': "Please don't kill snakes - they are a natural part of the ecosystem and [even species that use venom for prey acquisition and defense are beneficial to humans](https://umdrightnow.umd.edu/news/timber-rattlesnakes-vs-lyme-disease). One cannot expect outside to be sterile - if you see a snake you're probably in or around their preferred habitat. Most snakes are legally protected from collection, killing or harassment as non-game animals at the state level.\n\n[Neighborhood dogs](http://www.livingalongsidewildlife.com/2013/10/the-only-good-dog-is-dead-dog-why-it.html) are more likely to harm people. Professional snake relocation services are often free or inexpensive, but snakes often die trying to return to their original home range, so it is usually best to enjoy them like you would songbirds or any of the other amazing wildlife native to your area. Commercial snake repellents are not effective - to discourage snakes, eliminate sources of food and cover; clear debris, stacked wood and eliminate rodent populations. Seal up cracks in and around the foundation/base of your home."},
	{'command': "myths", 'text': "Here is a list of common myths and misconceptions about snakes. The below statements are false:\n\n[Non-venomous snakes shake their tails to mimic rattlesnakes](http://labs.bio.unc.edu/Pfennig/LabSite/Publications_files/2016_Am%20Nat.pdf)\n\n[Baby venomous snakes are more dangerous than adults](http://www.livingalongsidewildlife.com/2009/10/are-bites-from-baby-venomous-snakes.html#comment-1039213912)\n\n[Snakes Chase People](https://www.youtube.com/watch?v=314N7xIeRR8)\n\n[Rattlesnakes are losing their rattle because of {insert reason}](http://www.livingalongsidewildlife.com/2011/06/are-rattlesnakes-rattling-less-because.html)\n\n[The only good snake is a dead snake](https://umdrightnow.umd.edu/news/timber-rattlesnakes-vs-lyme-disease)"},
	{'command': "poisonous", 'text': "The verbiage currently used in biology is 'venom is injected poison is ingested'. So snakes with medically significant venom are typically referred to as venomous, but some species are also poisonous. Old books will use poisonous or 'snake venom poisoning' but that has fallen out of favor.\n\nThe best examples of poisonous snakes are *Rhabdophis* snakes from east Asia that [sequester and release toxins from their frog diet in nuchal glands in the neck](http://www.pnas.org/content/pnas/104/7/2265.full.pdf)."},
	{'command': "keels", 'text': "Keels are raised lines on the surface of scales that can be used as a character in snake identification to quickly narrow down options or distinguish between some similar looking species. Strength of keel is variable; usually referred to as 'strong' vs 'weak'.\n\nYou can read more about snake color patterns and scale architecture [here](https://www.floridamuseum.ufl.edu/herpetology/fl-snakes/color-pattern/)."},
	{'command': "cats", 'text': "Everyone loves cats, but they belong indoors. Each year in the United States [free-ranging domestic cats kill 1.3-4.0 billion birds and 6.3-22.3 billion mammals](https://www.nature.com/articles/ncomms2380.pdf). Numbers for reptiles are similar in Australia, as [2 million reptiles are killed **each day** by cats, totaling 650 million a year](https://www.researchgate.net/profile/Brett_Murphy/publication/325787707_How_many_reptiles_are_killed_by_cats_in_Australia/links/5b317b20aca2720785e837f1/How-many-reptiles-are-killed-by-cats-in-Australia.pdf). Outdoor cats are directly responsible for the extinction of at least 33 species worldwide and are considered one of the biggest threats to native wildlife."},
	{'command': "shed", 'text': "Snakes are identifiable from intact shed skins, but it takes some time and the correct knowledge.\n\nIf you're in North America, a basic guide to shed identification can be found [here](http://snakesarelong.blogspot.com/2012/11/identifying-snake-sheds-part-iii.html), but the people of /r/whatsthissnake will help if you post clear photos of the head, vent and midbody."},
	{'command': "gluetrap", 'text': "While effective in some applications, glue traps generally shouldn't be used outside or in garages, as by-catch of snakes and other harmless animals is difficult to avoid.\n\nSnakes stuck to glue traps are not always a lost cause and can be removed with mild cooking oil such as olive oil or lard. While applying more oil as you go, slowly and gently start with the tail and work your way forward. This should not be attempted by a novice on a venomous snake. Remember to use caution even with nonvenomous species - these animals do not understand your good intentions and will be exhausted, dehydrated and scared. They may try to bite you or themselves in self defense."},
	{'command': "resources", 'text': "There are a number of resources for snake ID and this list is nowhere near comprehensive.\n\nGlobally, comprehensive species lists are available via Reptile Database [Advanced Search](http://reptile-database.reptarium.cz/advanced_search). Reptile Database is mostly correct and up to date in terms of taxonomy. Another worldwide resource is [Snakes of the World](https://www.crcpress.com/Snakes-of-the-World-A-Catalogue-of-Living-and-Extinct-Species/Wallach-Williams-Boundy/p/book/9781138034006) which, in addition to being comprehensive for extant snakes, also provides a wealth of information on fossil taxa.\n\nRegional guides are useful. If you're in North America, the [Eastern Peterson Guide](https://www.amazon.com/Peterson-Reptiles-Amphibians-Eastern-Central/dp/0544129970) is a great tool, as is [Snakes of the United States and Canada](https://www.amazon.com/Snakes-United-States-Canada-Ernst/dp/1588340198). While [plagiarized and problematic](https://www.researchgate.net/profile/Joseph_Mendelson_Iii/publication/311993684_Review_of_Snakes_of_Mexico_volume_P_Heimes_author_by_J_R_Mendelson/links/5867e32c08ae329d620dfb40/Review-of-Snakes-of-Mexico-volume-P-Heimes-author-by-J-R-Mendelson.pdf), the book [Snakes of Mexico](http://www.chimaira.de/gp/herpetofauna-mexicana-vol-1-snakes-of-mexico.html) is the best easily accessible information for the region. For Central America, the [Kohler](https://www.amazon.com/Reptiles-Central-America-REVISED-2008/dp/3936180288) book as well as [Savage's Costa Rica book](https://www.amazon.com/Amphibians-Reptiles-Costa-Rica-Herpetofauna-dp-0226735389/dp/0226735389/) are excellent resources. South America is tough but has [a diagnostic catalog](https://www.biodiversitylibrary.org/page/7868973). Australia has [Cogger](https://www.publish.csiro.au/book/7845/) as a herp bible. SE Asia has two guides [one in German](https://www.amazon.com/Amphibien-Reptilien-S%C3%BCdostasiens-Wolfgang-Grossmann/dp/3931587126) and one [comprehensive](https://www.nhbs.com/a-field-guide-to-the-reptiles-of-south-east-asia-book). For Europe, you simply can't get better than the three volumes of [Handbuch der Reptilien und Amphibien Europas](https://www.nhbs.com/handbuch-der-reptilien-und-amphibien-europas-band-3i-schlangen-serpentes-i-book). Africa is also difficult - no comprehensive guide exists but there are a few good regional guides like [Reptiles of East Africa](https://www.amazon.com/Field-Guide-Reptiles-East-Africa/dp/0713668172/) and [Guide to the Reptiles of Southern Africa](https://www.amazon.com/Guide-Reptiles-Southern-Africa/dp/1770073868/). [Amphibians and Reptiles of Madagascar](https://www.amazon.com/Field-Guide-Amphibians-Reptiles-Madagascar/dp/392944903X) is a good source for that distinct region. For the Indian subcontinent, use [Snakes of India](https://www.amazon.com/Snakes-India-Field-Romulus-Whitaker/dp/8190187309/) \n\nRemember, species names are hypotheses that are tested and revised - old books become dated by the nature of science itself. One of your best resources is going to be checking here at /r/whatthissnake, or (for North America) with the [SSAR Standard Names List](https://ssarherps.org/cndb/) for the most recent accepted taxonomic changes.\n\n[Here](https://imgur.com/a/JDW7fBz) is an example of a small personal herpetology library."},
	{'command': "location", 'text': "Some species are best distinguishable from each other by geographic range, and not all species live all places. Providing a location allows for a quicker, more accurate ID. Thanks!"},
	{'command': "blackrat", 'text': "Black Ratsnake is a common name for a color pattern shared by three different species of *Pantherophis* ratsnake across the northern portion of their range.\n\nThe black ratsnake species complex, formerly *Elaphe obsoleta*, underwent revision in 2001-2002 from multiple authors and received two main changes. First, the complex was delimited in [Burbrink 2001](https://onlinelibrary.wiley.com/doi/pdf/10.1111/j.0014-3820.2000.tb01253.x) based on what were then modern molecular methods, where three distinct lineages were uncovered that did not reflect previous subspecies designations. Each of the three geographically partitioned taxa were elevated to full species status, and subspecies were discarded. The polytypic color patterns in these species are most likely under strong selection by the local environment and don't reflect evolutionary history. Where species intersect and habitat converges, color pattern also converges, leaving these species nearly morphologically indistinguishable to the naked eye. Second, using *Elaphe* as a genus name wasn't the best way to reflect phylogenetic history, so the genus *Pantherophis* was adopted for new world ratsnakes in [Utiger 2002](http://www.sierraherps.com/pdf/Utiger%20et%20al_2002.pdf). Remember, species names are hypotheses that are tested and revised. While the analyses published in 2001 are strong and results are geographically similar in other taxa, these species are currently being investigated using modern molecular methods and the taxonomy may be updated in the future.\n\nThe three currently accepted species in this complex are Western Ratsnake *Pantherophis obsoletus*, Central Ratsnake *Pantherophis spiloides* and Eastern Ratsnake *Pantherophis alleghaniensis*. [Range Map](https://imgur.com/ssyL1Q0)"},
]

specieslist = []
with open('species.txt', 'r') as filehandle:
	for line in filehandle:
		specieslist.append(line.strip())


def bot_login():
	print("Logging in...")
	r = praw.Reddit(username=config.username,
	                password=config.password,
	                client_id=config.client_id,
	                client_secret=config.client_secret,
	                user_agent="phylohelper v0.1")
	print("Logged in!")

	return r


def checkComment(comment):
	if comment.saved:
		return

	for species in specieslist:
		if "*" + species + "*" in comment.body:
			print("String with \"+ species""\" found in comment " + comment.id)
			with open(species + ".txt", "r") as f:
				comment_reply = f.read()
				comment.reply(comment_reply + "\n\n" + sig)
				print("Replied to comment " + comment.id)

	for command in commands:
		if "!" + command['command'] in comment.body:
			print("!" + command['command'] + " found in comment " + comment.id)
			comment.reply(command['text'])

	comment.save()


def run_bot(r):
	print("Obtaining 10 comments...")

	for username in list_of_names:
		user = r.redditor(username)
		for comment in user.comments.new(limit=10):
			checkComment(comment)

	for comment in r.subreddit('whatsthissnaketest').comments(limit=10):
		checkComment(comment)

	for submission in r.subreddit('whatsthissnaketest').new(limit=10):
		if submission.saved:
			break

		if len(re.findall('\[.+\]', submission.title)) == 0:
			submission.reply("It looks like you didn't provide a geographic location [in square brackets] in your title. "
			                 "Some species are best distinguishable from each other by geographic range, and not all "
			                 "species live all places. Providing a location allows for a quicker, more accurate ID."
			                 + "\n\n" + "If you provided a location but forgot the correct brackets, ignore this message "
			                            "until your next submission. Thanks!" + "\n\n" + sig)
			print("Replied to submission " + submission.id)

		if submission.link_flair_text == "Dead Snake":
			submission.reply("Please don't kill snakes - they are a natural part of the ecosystem and [even species that "
			                 "use venom for prey acquisition and defense are beneficial to humans]"
			                 "(https://umdrightnow.umd.edu/news/timber-rattlesnakes-vs-lyme-disease). One cannot expect "
			                 "outside to be sterile - if you see a snake you're in or around their preferred habitat. "
			                 "Most snakes are valued and as such are protected from collection, killing or harassment "
			                 "as non-game animals at the state level.\n\n[Neighborhood dogs]"
			                 "(http://www.livingalongsidewildlife.com/2013/10/the-only-good-dog-is-dead-dog-why-it.html) "
			                 "are more likely to harm people. Professional snake relocation services are often free or "
			                 "inexpensive, but snakes often die trying to return to their original home range, so it is "
			                 "usually best to enjoy them like you would songbirds or any of the other amazing wildlife "
			                 "native to your area. Commercial snake repellents are not effective - to discourage snakes, "
			                 "eliminate sources of food and cover; clear debris, stacked wood and eliminate rodent "
			                 "populations. Seal up cracks in and around the foundation/base of your home." + "\n\n" + sig)
			print("Replied to Dead Snake flair - " + submission.id)

		submission.save()


r = bot_login()

while True:
	try:
		run_bot(r)
	except Exception as err:
		print("Hit an error in main loop")
		print(traceback.format_exc())

	print("Sleeping for 30 seconds...")
	time.sleep(30)
