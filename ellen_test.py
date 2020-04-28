import matplotlib.pyplot as plt
import numpy as np
import csv
import glob

#csvfiles0 = r'C:\Users\Ellen\EllenStuff\PythonScripts\0\tek0000ALL.csv'#file location
files0 = glob.glob(r'C:\Users\Greg\Desktop\PyCharm\Sketchpad\ellen\*.csv')
numfiles0 = len(files0) #how many files
mydata0 = [] #init place to store data

temp_array = []
for filename in files0:
    hit_data = False
    with open(filename, newline='') as f:
        for line in f:
            stripped_line = line.strip()
            split = stripped_line.split(",")
            print(str(split))
            # if stripped_line == "<<DATA>>":
            #     hit_data = True
            #     continue
            # if stripped_line == "<<END>>":
            #     hit_data = False
            # if hit_data:
            #     temp_array.append(int(line))

        # reader = csv.reader(f)
        # data = list(reader)
        # mydata0.append(data)
        # print(data[20][0])

#del mydata0[0:15]
print(mydata0[0][0][0])

#Average through list in proper dimension

#repeat for different angles

#plot it all

if __name__ == "__main__":
    