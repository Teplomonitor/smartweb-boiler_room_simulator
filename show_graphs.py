
import csv
import os
import datetime
import sys
import random

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


logsRootDir = os.path.join(os.getcwd(), 'log')


def getRandomColor():
	r = random.random()
	b = random.random()
	g = random.random()

	color = (r, g, b)
	return color

def showPlots():
	ax=plt.gca()
	ax.xaxis.axis_date()

	for (dirPath, dirNames, fileNames) in os.walk(logsRootDir):
		### Filter file name list for files ending with .csv
		fileNames = [file for file in fileNames if '.csv' in file]
		
		### Loop over all files
		for file in fileNames:
		
			### Read .csv file and append to list
			with open(os.path.join(dirPath, file), encoding='utf-8', newline='') as fp:
				reader = csv.reader(fp, delimiter=",", quotechar='"')
				next(reader, None)  # skip the headers
				lines = [row for row in reader]
				### Create line for every file
				if len(lines) > 1:
					x = []
					y = []
					for row in lines:
						x.append(datetime.datetime.fromtimestamp(int(row[0])))
						y.append(float(row[1]))
					converted_dates = mdates.date2num(x)
					
					plt.plot(converted_dates, y, c=getRandomColor(),
						#	linestyle = 'dashed',
							marker = 'o',
							label = file)
	
	### Generate the plot
	plt.xlabel('Time')
	plt.ylabel('Temperature(°C)')
	plt.title('Simulator log', fontsize = 20)
	plt.grid()
	plt.legend()
	plt.show()
		

def main(argv=None): # IGNORE:C0111
	showPlots()
	return 0
	
if __name__ == "__main__":
	sys.exit(main())