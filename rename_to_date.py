import os
from datetime import datetime
import exifread

if __name__ == "__main__":
	folder = r"C:\Users\greg\Desktop\Drive\Loop"
	for file in os.listdir(folder):
		file_path = os.path.join(folder, file)

		with open(file_path, 'rb') as fh:
			tags = exifread.process_file(fh, stop_tag="EXIF DateTimeOriginal")
			date_taken = tags["EXIF DateTimeOriginal"]
			datetime_taken = datetime.strptime(str(date_taken), "%Y:%m:%d %H:%M:%S")

		datetime_name = datetime_taken.strftime('%Y%m%d_%H%M')
		print(f"{file} : {datetime_name}.jpg")
		os.rename(file_path, os.path.join(folder, datetime_name) + ".jpg")
