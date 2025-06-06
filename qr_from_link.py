import qrcode

if __name__ == "__main__":
	folder = r"C:\Users\greg\Desktop\Files\backup"

	urls = """""".split("\n")

	# img = qrcode.make("otpauth://totp/watchful%40watchful.gr?algorithm=SHA1&digits=6&issuer=Discord&secret=H666LHKVQO5BN4AD")
	# img.save(r"C:\Users\greg\Desktop\Files\backup\test.png")

	for url in urls:
		parts = url.split("&")
		site = None
		user = None
		for part in parts:
			inner_parts = part.split("=")
			if len(inner_parts) == 2:
				name, value = inner_parts[0], inner_parts[1]
				if name == "issuer":
					site = value
		before, after = url.split("?")
		before, after = before.split("totp/")
		user = after
		user = user.replace("%40","@")
		filename = f"{folder}\\{site}_{user}.png"
		print(filename)

		img = qrcode.make(url)
		img.save(filename)




