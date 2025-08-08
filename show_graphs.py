
import csv
import os
import datetime
import sys
import random

from typing import Union
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.dates as mdates


logsRootDir = os.path.join(os.getcwd(), 'log')


def getRandomColor():
	r = random.random()
	b = random.random()
	g = random.random()

	color = (r, g, b)
	return color

def get_n_last_subparts_path(base_dir: Union[Path, str], n:int) -> Path:
	return Path(*Path(base_dir).parts[-n-1:])

def valueToPlot(value, valueFormat):
	if valueFormat == 'RELAY':
		return float(value)/255*100
	return float(value)
	
def showPlots():
	ax=plt.gca()
	ax.xaxis.axis_date()

	for (dirPath, dirNames, fileNames) in os.walk(logsRootDir):
		### Filter file name list for files ending with .csv
		fileNames = [file for file in fileNames if '.csv' in file]
		
		### Loop over all files
		for file in fileNames:
		
			### Read .csv file and append to list
			filePath = os.path.join(dirPath, file)
			with open(filePath, encoding='utf-8', newline='') as fp:
				reader = csv.reader(fp, delimiter=",", quotechar='"')
				header = next(reader, None)  # skip the headers
				valueFormat = header[1]
				lines = [row for row in reader]
				### Create line for every file
				if len(lines) > 1:
					x = []
					y = []
					
					for row in lines:
						x.append(datetime.datetime.fromtimestamp(int(row[0])))
						y.append(valueToPlot(row[1], valueFormat))
					converted_dates = mdates.date2num(x)
					
#					splitext = os.path.splitext(filePath)
#					num = len(splitext)
					
#					label = '_'.join(splitext[num-2])
#					label = splitext[0]
					label = str(get_n_last_subparts_path(filePath, 2))
					
					if valueFormat == 'RELAY':
						plt.step(converted_dates, y, c=getRandomColor(),
						#	linestyle = 'dashed',
							where = 'post', #The y value is continued constantly to the right from every x position
							marker = 'o',
							label = label)
					else:
						plt.plot(converted_dates, y, c=getRandomColor(),
						#	linestyle = 'dashed',
							marker = '.',
							label = label)
	
	### Generate the plot
	plt.xlabel('Time')
	plt.ylabel('Value')
	plt.title('Simulator log', fontsize = 20)
	plt.grid()
	plt.legend()
	plt.show()
		

def main(argv=None): # IGNORE:C0111
	showPlots()
	return 0
	
if __name__ == "__main__":
	sys.exit(main())