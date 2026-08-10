import csv
import datetime
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pyqtgraph as pg
from PySide6 import QtCore, QtGui, QtWidgets


logs_root_dir = Path.cwd() / "log"
MAX_MARKERS_PER_TREND = 200
BASE_LINE_WIDTH = 1.5
HIGHLIGHT_LINE_WIDTH = 3.0


class DateAxisItem(pg.AxisItem):
	"""Format Unix timestamps as local date/time labels."""

	def tickStrings(self, values, scale, spacing):
		labels = []
		for value in values:
			try:
				stamp = datetime.datetime.fromtimestamp(float(value))
			except (OverflowError, OSError, ValueError):
				labels.append("")
				continue

			if spacing >= 24 * 60 * 60:
				labels.append(stamp.strftime("%Y-%m-%d"))
			elif spacing >= 60 * 60:
				labels.append(stamp.strftime("%m-%d %H:%M"))
			else:
				labels.append(stamp.strftime("%H:%M:%S"))
		return labels


@dataclass
class Trend:
	label: str
	values_x: list[float]
	values_y: list[float]
	color: str
	is_relay: bool
	curve: Any
	line_width: float = BASE_LINE_WIDTH


def value_to_plot(value, value_format):
	if value_format == "RELAY":
		return float(value) / 255 * 100
	return float(value)


def get_marker_interval(point_count):
	if point_count <= MAX_MARKERS_PER_TREND:
		return 1
	return (point_count + MAX_MARKERS_PER_TREND - 1) // MAX_MARKERS_PER_TREND


def get_n_last_subparts_path(base_dir, n):
	return Path(*Path(base_dir).parts[-n - 1:])


def _read_trend_data():
	trend_data = []
	if not logs_root_dir.is_dir():
		return trend_data

	for dir_path, _, file_names in os.walk(logs_root_dir):
		for file_name in sorted(file for file in file_names
				if file.lower().endswith(".csv")):
			file_path = Path(dir_path) / file_name
			try:
				with file_path.open(encoding="utf-8", newline="") as fp:
					reader = csv.reader(fp)
					header = next(reader, None)
					if not header or len(header) < 2:
						continue
					value_format = header[1].strip()
					x_values = []
					y_values = []
					for row in reader:
						if len(row) < 2:
							continue
						try:
							x_values.append(float(row[0]))
							y_values.append(value_to_plot(row[1], value_format))
						except (TypeError, ValueError):
							continue
			except (OSError, UnicodeError):
				continue

			if len(x_values) <= 1:
				continue
			label = str(get_n_last_subparts_path(file_path, 2))
			trend_data.append((label, x_values, y_values, value_format == "RELAY"))

	return trend_data


class GraphWindow(QtWidgets.QMainWindow):
	def __init__(self):
		super().__init__()
		self.setWindowTitle("Simulator log")
		self.resize(1400, 800)
		self.trends = []
		self.selected_trend = None
		self._colors = [
			"#377eb8", "#e41a1c", "#4daf4a", "#984ea3", "#ff7f00",
			"#a65628", "#f781bf", "#17becf", "#bcbd22", "#7f7f7f",
		]

		self.plot = pg.PlotWidget(axisItems={"bottom": DateAxisItem(orientation="bottom")})
		self.plot.setLabel("bottom", "Time")
		self.plot.setLabel("left", "Value")
		self.plot.setTitle("Simulator log")
		self.plot.showGrid(x=True, y=True, alpha=0.25)
		self.plot.setBackground("w")
		self.plot.getAxis("left").setPen(pg.mkPen("#444444"))
		self.plot.getAxis("bottom").setPen(pg.mkPen("#444444"))
		self.plot.scene().sigMouseClicked.connect(self._plot_clicked)

		self.trend_list = QtWidgets.QListWidget()
		self.trend_list.setMinimumWidth(300)
		self.trend_list.currentRowChanged.connect(self._select_trend)
		self.trend_list.itemChanged.connect(self._set_trend_visibility)

		self.reload_button = QtWidgets.QPushButton("Reload")
		self.reload_button.clicked.connect(self.reload)
		self.auto_range_button = QtWidgets.QPushButton("Auto range")
		self.auto_range_button.clicked.connect(self.plot.autoRange)
		self.status_label = QtWidgets.QLabel()

		controls = QtWidgets.QHBoxLayout()
		controls.addWidget(self.reload_button)
		controls.addWidget(self.auto_range_button)
		controls.addStretch()
		controls.addWidget(self.status_label)

		left_panel = QtWidgets.QVBoxLayout()
		left_panel.addWidget(QtWidgets.QLabel("Trends"))
		left_panel.addWidget(self.trend_list)
		left_panel.addLayout(controls)

		container = QtWidgets.QWidget()
		layout = QtWidgets.QHBoxLayout(container)
		layout.addLayout(left_panel)
		layout.addWidget(self.plot, stretch=1)
		self.setCentralWidget(container)
		self.reload()

	def reload(self):
		self.plot.clear()
		self.plot.setTitle("Simulator log")
		self.trend_list.blockSignals(True)
		self.trend_list.clear()
		self.trends.clear()
		self.selected_trend = None

		for index, (label, x_values, y_values, is_relay) in enumerate(_read_trend_data()):
			color = self._colors[index % len(self._colors)]
			marker_interval = get_marker_interval(len(y_values))
			pen = pg.mkPen(color=color, width=BASE_LINE_WIDTH)
			curve_kwargs = {
				"pen": pen,
			}
			if is_relay:
				curve_kwargs.update({
					"symbol": "o",
					"symbolSize": 6,
					"symbolPen": pen,
					"symbolBrush": color,
				})
			if marker_interval > 1:
				curve_kwargs["skipFiniteCheck"] = True
				plot_x = x_values[::marker_interval]
				plot_y = y_values[::marker_interval]
			else:
				plot_x = x_values
				plot_y = y_values
			if is_relay:
				curve_kwargs["stepMode"] = "right"
			curve = self.plot.plot(plot_x, plot_y, **curve_kwargs)
			trend = Trend(label, x_values, y_values, color, is_relay, curve)
			self.trends.append(trend)

			item = QtWidgets.QListWidgetItem(label)
			item.setFlags(item.flags() | QtCore.Qt.ItemFlag.ItemIsUserCheckable)
			item.setCheckState(QtCore.Qt.CheckState.Checked)
			item.setForeground(QtGui.QColor(color))
			item.setData(QtCore.Qt.ItemDataRole.UserRole, trend)
			self.trend_list.addItem(item)

		self.trend_list.blockSignals(False)
		if self.trends:
			self.status_label.setText(f"{len(self.trends)} trend(s)")
			self.plot.autoRange()
		else:
			self.status_label.setText(f"No CSV trends found in {logs_root_dir}")
			self.plot.setTitle("Simulator log — no trends found")

	def _set_trend_visibility(self, item):
		trend = item.data(QtCore.Qt.ItemDataRole.UserRole)
		if trend is not None:
			trend.curve.setVisible(item.checkState() == QtCore.Qt.CheckState.Checked)

	def _select_trend(self, row):
		self._set_highlight(self.trend_list.item(row).data(QtCore.Qt.ItemDataRole.UserRole)
			if row >= 0 else None)

	def _set_highlight(self, selected):
		self.selected_trend = selected
		for trend in self.trends:
			width = HIGHLIGHT_LINE_WIDTH if trend is selected else trend.line_width
			trend.curve.setPen(pg.mkPen(color=trend.color, width=width))

	def _plot_clicked(self, event):
		if event.button() != QtCore.Qt.MouseButton.LeftButton:
			return
		mouse_point = self.plot.plotItem.vb.mapSceneToView(event.scenePos())
		if not self.trends:
			return
		nearest = min(
			self.trends,
			key=lambda trend: min(
				(abs(x - mouse_point.x()) for x in trend.values_x),
				default=float("inf"),
			),
		)
		self.trend_list.setCurrentRow(self.trends.index(nearest))


def show_plots():
	app = QtWidgets.QApplication.instance() or QtWidgets.QApplication(sys.argv)
	window = GraphWindow()
	window.show()
	return app.exec()


def main(argv=None):
	return show_plots()


if __name__ == "__main__":
	sys.exit(main())