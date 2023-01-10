import praw

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1", ratelimit_seconds=60)

	comments = [
		"[With the new Butterfinger sponsor... I'm a little concerned the new hero reveal will look like this](https://www.reddit.com/r/Competitiveoverwatch/comments/ylio1c/with_the_new_butterfinger_sponsor_im_a_little/) by u/ZenofyMedia",
		"[Homlette](https://www.reddit.com/r/Competitiveoverwatch/comments/yo1q1h/homlette/) by u/ComradeHines",
		"[I Fixed the Lan Setup](https://www.reddit.com/r/Competitiveoverwatch/comments/w2bnp5/i_fixed_the_lan_setup/) by u/bullxbull",
		"[The 2022 Overwatch League Kickoff Clash Experience](https://www.reddit.com/r/Competitiveoverwatch/comments/v790nw/the_2022_overwatch_league_kickoff_clash_experience/) by u/MrZeddus",
		"[PSA for all OWL Doomfists. If you are in overtime, this is your keyboard.](https://www.reddit.com/r/Competitiveoverwatch/comments/vpo188/psa_for_all_owl_doomfists_if_you_are_in_overtime/) by u/Ezraah",
		"[IM IN BBY](https://www.reddit.com/r/Competitiveoverwatch/comments/v3eueb/im_in_bby/) by u/lightning0614",
		"[🦍 WINTON 🦍 jump 🦍 WINTON 🦍 zap 🦍 WINTON 🦍 ult 🦍 WINTON 🦍 nap 🦍](https://www.reddit.com/r/Competitiveoverwatch/comments/v4oned/winton_jump_winton_zap_winton_ult_winton_nap_not/) by u/MmeM1m",
		"[UPDATED: Teams Ranked Based On Whether Or Not They Are A Professional Organization](https://www.reddit.com/r/Competitiveoverwatch/comments/uxsd2p/updated_teams_ranked_based_on_whether_or_not_they/) by u/Coathar44",
		"[HANGOAT](https://www.reddit.com/r/Competitiveoverwatch/comments/uvkqtn/hangoat/) by u/XXGrassXX",
		"[Did anyone else get this email?](https://www.reddit.com/r/Competitiveoverwatch/comments/ucrap2/did_anyone_else_get_this_email/) by u/_Gondamar_",
		"[A leaked interview with a Blizzard Path to Pro employee...](https://www.reddit.com/r/Competitiveoverwatch/comments/um4wnp/a_leaked_interview_with_a_blizzard_path_to_pro/) by u/Weevil2000",
		"[impressive that the devs managed to make a 0 skill meta dont even call this salty cause its legitmately true. you see teams like glads shock and reign dropping maps and series to teams that should never be able to touch them and its really the only conclusion you can come to 🧐](https://www.reddit.com/r/Competitiveoverwatch/comments/wnsnrk/reiner_impressive_that_the_devs_managed_to_make_a/) by Reiner",
		"[Get you a rival that has a matching profile pic](https://www.reddit.com/r/Competitiveoverwatch/comments/w5upze/get_you_a_rival_that_has_a_matching_profile_pic/) by Reiner and Coluge",
		"[Mr. SBD strikes again](https://www.reddit.com/r/Competitiveoverwatch/comments/w4up7d/mr_sbd_strikes_again/) by Lastro",
		"[Seagull learns who ANS is](https://www.reddit.com/r/Competitiveoverwatch/comments/uckolp/seagull_learns_who_ans_is/) by Seagull",
	]

	post = reddit.submission("102shdk")
	i = 1
	for comment in comments:
		post.reply(comment)
		print(f"{i}/{len(comments)}")
		i += 1
