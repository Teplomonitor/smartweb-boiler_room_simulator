
import csv
import os
import datetime
import sys
import random

from dataclasses import dataclass
from typing import Union
from pathlib import Path

from matplotlib.lines import Line2D
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


logsRootDir = os.path.join(os.getcwd(), 'log')
MAX_MARKERS_PER_TREND = 200


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


def get_marker_interval(point_count):
	if point_count <= MAX_MARKERS_PER_TREND:
		return 1
	return (point_count + MAX_MARKERS_PER_TREND - 1) // MAX_MARKERS_PER_TREND


@dataclass
class Trend:
	label: str
	line: Line2D
	color: tuple
	line_width: float = 1.5
	legend_line: Line2D = None
	legend_text: object = None
	legend_line_width: float = 1.5


def _read_trends(ax):
	trends = []

	for (dirPath, dirNames, fileNames) in os.walk(logsRootDir):
		fileNames = sorted(file for file in fileNames if file.lower().endswith('.csv'))

		for file in fileNames:
			filePath = os.path.join(dirPath, file)
			with open(filePath, encoding='utf-8', newline='') as fp:
				reader = csv.reader(fp, delimiter=",", quotechar='"')
				header = next(reader, None)
				if not header or len(header) < 2:
					continue
				valueFormat = header[1]
				lines = [row for row in reader if len(row) >= 2]
				if len(lines) <= 1:
					continue

				x = []
				y = []
				for row in lines:
					x.append(datetime.datetime.fromtimestamp(int(row[0])))
					y.append(valueToPlot(row[1], valueFormat))
				converted_dates = mdates.date2num(x)
				marker_interval = get_marker_interval(len(y))
				label = str(get_n_last_subparts_path(filePath, 2))
				color = getRandomColor()

				if valueFormat == 'RELAY':
					line = ax.step(converted_dates, y, c=color,
						where='post', marker='o', markevery=marker_interval,
						label=label, picker=True)[0]
				else:
					line = ax.plot(converted_dates, y, c=color,
						marker='.', markevery=marker_interval,
						label=label, picker=True)[0]
				trends.append(Trend(label, line, color, line.get_linewidth()))

	return trends


def _set_highlight(trends, selected):
	line_width_increase = 2
	
	for trend in trends:
		is_selected = trend is selected
		trend.line.set_linewidth(
			trend.line_width + line_width_increase if is_selected else trend.line_width)
		if trend.legend_line is not None:
			trend.legend_line.set_linewidth(
				trend.legend_line_width + line_width_increase if is_selected
				else trend.legend_line_width)


def _add_interactions(fig, ax, trends, legend):
	legend_lines = legend.get_lines()
	legend_texts = legend.get_texts()
	for trend, legend_line, legend_text in zip(trends, legend_lines, legend_texts):
		trend.legend_line = legend_line
		trend.legend_text = legend_text
		trend.legend_line_width = legend_line.get_linewidth()
		legend_line.set_picker(True)
		legend_text.set_picker(True)
		legend_line.set_color(trend.color)
		legend_text.set_color(trend.color)

	selected = [None]

	def find_trend(artist):
		for trend in trends:
			if (artist is trend.line or artist is trend.legend_line or
					artist is trend.legend_text):
				return trend
		return None

	def on_pick(event):
		trend = find_trend(event.artist)
		if trend is None:
			return
		if event.mouseevent.button == 3:
			trend.line.set_visible(not trend.line.get_visible())
		else:
			selected[0] = None if selected[0] is trend else trend
			_set_highlight(trends, selected[0])
		fig.canvas.draw_idle()

	fig.canvas.mpl_connect('pick_event', on_pick)


def showPlots():
	fig, ax = plt.subplots()
	fig.subplots_adjust(right=0.72)
	ax.xaxis.axis_date()
	trends = _read_trends(ax)

	ax.set_xlabel('Time')
	ax.set_ylabel('Value')
	ax.set_title('Simulator log', fontsize=20)
	ax.grid()
	legend = ax.legend(loc='upper left', bbox_to_anchor=(1.02, 1.0),
		borderaxespad=0)
	if trends:
		_add_interactions(fig, ax, trends, legend)
	else:
		ax.text(0.5, 0.5, 'No log trends found',
			ha='center', va='center', transform=ax.transAxes)
	plt.show()
		

def main(argv=None): # IGNORE:C0111
	showPlots()
	return 0
	
if __name__ == "__main__":
	sys.exit(main())