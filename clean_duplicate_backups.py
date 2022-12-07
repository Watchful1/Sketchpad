import discord_logging
from datetime import datetime, timedelta
import os

log = discord_logging.init_logging()

if __name__ == "__main__":
	backup_folder = r"D:\backup\UpdateMeBot"
	delete_folder = r"D:\backup\UpdateMeBotDelete"

	known_day = None
	for subdir, dirs, files in os.walk(backup_folder):
		for filename in reversed(files):
			if filename.endswith(".db"):
				backup_date = datetime.strptime(filename[:-3], "%Y-%m-%d_%H-%M")
				day = backup_date.strftime("%Y-%m-%d")
				if day == known_day:
					log.info(f"Deleting: {filename}")
					try:
						os.rename(os.path.join(subdir, filename), os.path.join(delete_folder, filename))
					except FileExistsError:
						log.info("File exists, skipping")

				else:
					log.info(f"Keeping: {filename}")
					known_day = day
