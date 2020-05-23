import os
import re
import eyed3

source_dir = r'C:\Users\greg\Downloads\2 - The Old Republic Revan'
dest_dir = r'C:\Users\greg\Downloads\Revan'
image = r'C:\Users\greg\Downloads\Audiobooks\Legends\1 Old Republic Era (2,500 to 800 BBY)\2 - The Old Republic Revan\Star Wars The Old Republic Revan.jpg'

i = 1
for subdir, dirs, files in os.walk(source_dir):
	for file in files:
		old_path = os.path.join(subdir, file)
		disc_num = int(re.search(r"(?:Disc )(\d+)", subdir).group(1))
		track_num = int(re.search(r"(?:Track )(\d+)", file).group(1))
		audio_file = eyed3.load(old_path)
		audio_file.tag.title = f"Revan Track{i:03}"
		audio_file.tag.album = "The Old Republic Revan"
		audio_file.tag.artist = "Drew Karpyshyn"
		audio_file.tag.track_num = i
		audio_file.tag.images.set(3, open(image, 'rb').read(), 'image/jpeg')
		audio_file.tag.save()

		new_path = os.path.join(dest_dir, f"Revan_Track{i:03}.mp3")
		os.rename(old_path, new_path)
		print(new_path)

		i += 1
