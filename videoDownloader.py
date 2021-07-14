import praw
import requests
import re
import moviepy.editor as mpe
import os

reddit = praw.Reddit("Watchful1BotTest")

output = "videos"


def download_video(reddit_video_url, output_folder, output_name):
	video_file_name = f"{output_folder}/temp_video.mp4"
	with open(video_file_name, 'wb') as video_file:
		video_file.write(requests.get(reddit_video_url).content)

	audio_url = re.sub(r"(v.redd.it/\w+/)(\w+)(\.mp4)", r"\1DASH_audio\3", reddit_video_url)
	audio_file_name = f"{output_folder}/temp_audio.mp4"
	with open(audio_file_name, 'wb') as audio_file:
		audio_file.write(requests.get(audio_url).content)

	output_file_name = f"{output_name}.mp4"

	video_clip = mpe.VideoFileClip(video_file_name)
	audio_clip = mpe.AudioFileClip(audio_file_name)
	final_clip = video_clip.set_audio(audio_clip)
	print(f"Saving: {output_file_name}")
	final_clip.write_videofile(f"{output_folder}/{output_file_name}", logger=None)

	os.remove(video_file_name)
	os.remove(audio_file_name)


def get_video_url(submission):
	if not submission.is_video:
		return None

	if not hasattr(submission, "media") or 'reddit_video' not in submission.media or 'fallback_url' not in submission.media['reddit_video']:
		return None

	groups = re.search(r"https?://v.redd.it/\w+/\w+.mp4", submission.media['reddit_video']['fallback_url'])
	if not groups:
		return None

	return groups.group(0)


for submission in reddit.subreddit("nextfuckinglevel").top(limit=25):
	video_url = get_video_url(submission)
	if video_url is not None:
		download_video(video_url, output, submission.title)
