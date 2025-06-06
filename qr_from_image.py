from qreader import QReader
import cv2


if __name__ == "__main__":
	# Create a QReader instance
	qreader = QReader()

	# Get the image that contains the QR code
	#image = cv2.cvtColor(cv2.imread(r"C:\Users\greg\Desktop\Drive\Screenshot_20250208-163122.png"), cv2.COLOR_BGR2RGB)
	image = cv2.cvtColor(cv2.imread(r"C:\Users\greg\Desktop\Drive\Screenshot_20250208-163132.png"), cv2.COLOR_BGR2RGB)

	# Use the detect_and_decode function to get the decoded QR data
	decoded_text = qreader.detect_and_decode(image=image)

	print(decoded_text)
