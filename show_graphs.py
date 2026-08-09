
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
from matplotlib.widgets import CheckButtons


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


@dataclass
class Trend:
	label: str
	line: Line2D
	color: tuple
	control_label: str = None
	legend_line: Line2D = None
	legend_text: object = None


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
				label = str(get_n_last_subparts_path(filePath, 2))
				color = getRandomColor()

				if valueFormat == 'RELAY':
					line = ax.step(converted_dates, y, c=color,
						where='post', marker='o', label=label, picker=True)[0]
				else:
					line = ax.plot(converted_dates, y, c=color,
						marker='.', label=label, picker=True)[0]
				trends.append(Trend(label, line, color))

	return trends


def _set_highlight(trends, selected):
	for trend in trends:
		is_selected = trend is selected
		trend.line.set_alpha(1.0 if selected is None or is_selected else 0.2)
		trend.line.set_linewidth(2.5 if is_selected else 1.5)
		if trend.legend_line is not None:
			trend.legend_line.set_alpha(1.0 if selected is None or is_selected else 0.2)


def _add_interactions(fig, ax, trends, legend):
	checkbox_axis = fig.add_axes([0.01, 0.15, 0.24, 0.7])
	labels_seen = {}
	control_labels = []
	for trend in trends:
		labels_seen[trend.label] = labels_seen.get(trend.label, 0) + 1
		count = labels_seen[trend.label]
		trend.control_label = trend.label if count == 1 else f'{trend.label} ({count})'
		control_labels.append(trend.control_label)
	checkbox = CheckButtons(checkbox_axis,
		control_labels, [True] * len(trends))
	checkbox_axis.set_title('Show trends', fontsize=10)
	for label, trend in zip(checkbox.labels, trends):
		label.set_color(trend.color)

	legend_lines = legend.get_lines()
	legend_texts = legend.get_texts()
	for trend, legend_line, legend_text in zip(trends, legend_lines, legend_texts):
		trend.legend_line = legend_line
		trend.legend_text = legend_text
		legend_line.set_picker(True)
		legend_text.set_picker(True)
		legend_line.set_color(trend.color)
		legend_text.set_color(trend.color)

	selected = [None]

	def toggle_trend(label):
		for trend in trends:
			if trend.control_label == label:
				trend.line.set_visible(not trend.line.get_visible())
				break
		fig.canvas.draw_idle()

	def highlight_artist(artist):
		for trend in trends:
			if (artist is trend.line or artist is trend.legend_line or
					artist is trend.legend_text):
				selected[0] = None if selected[0] is trend else trend
				_set_highlight(trends, selected[0])
				fig.canvas.draw_idle()
				break

	checkbox.on_clicked(toggle_trend)

	def on_pick(event):
		highlight_artist(event.artist)

	fig.canvas.mpl_connect('pick_event', on_pick)
	return checkbox


def showPlots():
	fig, ax = plt.subplots()
	fig.subplots_adjust(left=0.29, right=0.98)
	ax.xaxis.axis_date()
	trends = _read_trends(ax)

	ax.set_xlabel('Time')
	ax.set_ylabel('Value')
	ax.set_title('Simulator log', fontsize=20)
	ax.grid()
	legend = ax.legend(loc='upper left', bbox_to_anchor=(1.0, 1.0))
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