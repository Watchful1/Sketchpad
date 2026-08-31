import matplotlib.pyplot as plt
import numpy as np
import csv
import glob
import re
from collections import defaultdict


def get_hist_data(folder, voltages):
    file_path = r'C:\Users\greg\Desktop\PyCharm\Sketchpad\ellen\\' + folder + '\\*.mca'
    expression = r'([\d\-\.]+)(.mca)'
    files0 = glob.glob(file_path)
    data_array = [0]*len(files0)
    angles = []
    i = 0

    for filename in files0:
        filename_angle = re.search(expression, filename)
        angles.append(filename_angle[1])
        hit_data = False
        temp_array = []
        with open(filename, newline= '') as f:
            for line in f:
                stripped_line = line.strip()
                if stripped_line == "<<DATA>>":
                    hit_data = True
                    continue
                if stripped_line == "<<END>>":
                    hit_data = False
                if hit_data:
                    temp_array.append(int(line))
        data_array[i]=temp_array
        voltages[filename_angle[1]].append(temp_array)
        i += 1

    data_arrayT = np.transpose(data_array)

    return data_arrayT, angles


foldersa = ['start', 'stop']
foldersb = ['vmcp_2000', 'vmcp_2100', 'vmcp_2220', 'vmcp_2300', 'vmcp_2400', 'vmcp_2500', 'vmcp_2600']
folders = foldersa + foldersb

data = defaultdict(list)
voltages = defaultdict(list)
for item in foldersb:
    data[item], angles = get_hist_data(item, voltages)

# pos = 1
# for item in foldersa:
#     plt.subplot(len(foldersa),1,pos)
#     plt.plot(data[item])
#     plt.xlim(0,2000)
#     plt.title(item)
#     pos += 1
# plt.legend(angles_l[item])
# plt.show()

pos = 1
for item in foldersb:
    plt.subplot(len(foldersb),1,pos)
    plt.plot(data[item])
    plt.xlim(2400,3200)
    plt.title(item)
    pos += 1

plt.legend(angles)
plt.show()

pos = 1
for angle in angles:
    plt.subplot(len(angles),1,pos)
    plt.plot(np.transpose(voltages[angle]))
    plt.xlim(2400,3200)
    pos += 1

plt.show()
