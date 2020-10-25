# -*- coding: utf-8 -*-
"""

Created on Mon Oct 19 09:28:35 2020

@author: efrobert
"""

import matplotlib.pyplot as plt
import numpy as np
import glob
import statistics

file_path = r'C:\Users\greg\Downloads\ellen\*'
files = glob.glob(file_path)  # create a list of the filenames in the above folder
channels = 4
samples = 10000000
bits = 12
a = 1

attenuations = [0, 3, 6, 10, 13, 16, 20, 23, 26, 30, 33, 36, 40, 43, 46, 50, 53, 56, 60, 63, 66, 70, 73, 76, 80, 83, 86,
				90, 93, 96, 100]

AGC = []
Voutrms = []


def get_average(numbers):
	subtract_number = 0
	for i in range(50):
		subtract_number += numbers[i]
	subtract_number = subtract_number / 50

	total = 0
	for i, num in enumerate(numbers):
		total += (num - subtract_number)
		if i % 1000000 == 0:
			print(f"{i}/{len(numbers)}")

	average = total / len(numbers) + subtract_number
	print(f"{len(numbers)}/{len(numbers)} = {average}")
	return average


# for each file, read, parse, check if trace is near ground station, save data
for filename in files:
	x = np.fromfile(filename, dtype=np.dtype("<i2"), count=channels * samples)
	actualsamples = int(x.shape[0] / 4)
	x = np.reshape(x, [actualsamples, channels])  # read single channel as x[:,<channel_number>]

	x = x - 2 ** (bits - 1)  # Deal with offset binary, still not 0 mean due to DC offset at ADC input
	# channel 1 = stack output
	# channel 2 = input pre-attenuator
	# channel 3 = AGC
	# channel 4 = input post-attenuator

	AGCsingle = get_average(x[:, 2])

	# Voutrmssingle = np.sqrt(np.mean(x[:, 0] ** 2))
	#
	# if (a % 2) == 1:
	# 	AGCsave = AGCsingle
	#
	# 	Voutrmssave = Voutrmssingle
	# if (a % 2) == 0:
	# 	AGC.append((AGCsingle + AGCsave) / 2)
	# 	Voutrms.append((Voutrmssingle + Voutrmssave) / 2)
