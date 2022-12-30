import praw

if __name__ == "__main__":
	reddit = praw.Reddit("Watchful1", ratelimit_seconds=60)

	comments = [
		"[Kickoff clash, final moments of Defiant vs Outlaws](https://www.youtube.com/clip/Ugkx8EiBBwig5w9LaJJyfwjvXynq03f_SGgZ)",
		"[Summer showdown, Hanbin carry vs Shock](https://www.youtube.com/clip/Ugkx5L1ZIUIxdlfup3L4e-V4gYgdfejyEeob)",
		"[Mer1t triple headshot versus uprising](https://www.youtube.com/clip/UgkxAL9XnqeEk8BwPAZqDf0Io5Ef_VYd8u2Z)",
		"[Sombra v Sombra action, Dragons vs Dynasty](https://www.reddit.com/r/Competitiveoverwatch/comments/xow4kv/when_the_hunter_becomes_the_hunted_countdown_cup/)",
		"[Decay railgun carry vs Fuel](https://www.youtube.com/clip/UgkxHSPTK5y3YzlO_aDGlbR2sh_Iks2zboZr)",
		"[Dragons insane recontest win vs Dynasty](https://www.reddit.com/r/Competitiveoverwatch/comments/xaoc4m/they_probably_wont_touch_at_all_even_avrl_is/)",
		"[Zest stall versus Charge](https://www.youtube.com/clip/UgkxMNNLcEE_mqdghoqgEmeZYUNV98bEn5Rg)",
		"[Lip clicks heads versus Dynasty](https://www.reddit.com/r/Competitiveoverwatch/comments/xbjoet/average_lip_gameplay_clip_summer_showdown_grand/)",
		"[MN3 pulls a Carpe vs Mayhem](https://www.youtube.com/clip/UgkxMFrhOor1Hj0wEj0kkZha0wU3muQ15Gxk)",
		"[MN3 4k widow headshot vs Dynasty](https://www.reddit.com/r/Competitiveoverwatch/comments/vvwiyr/we_shall_now_refer_to_such_moments_as_mn3_time/)",
		"[Profit 180 widow reflect vs Fusion](https://www.youtube.com/clip/Ugkx8FmqS4noymUL4U7aRLmZpr36CgZ2-VU4)",
		"[Checkmate blocks grav with Mei wall vs Fuel](https://www.reddit.com/r/Competitiveoverwatch/comments/v4xc8a/checkmate_blocks_graviton_surge_with_mei_wall/)",
	]

	post = reddit.submission("zxh2yj")
	i = 1
	for comment in comments:
		post.reply(comment)
		print(f"{i}/{len(comments)}")
		i += 1
