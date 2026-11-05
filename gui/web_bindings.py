"""Tk dashboard; importing this module never imports wx or CAN services."""

import copy
import json
from pathlib import Path
import queue
import subprocess
import sys
import tempfile
import threading
import tkinter as tk
from tkinter import messagebox, ttk

from web_binding_bench import (LABELS, ROOT, ROLES, SETTINGS_PATH, default_settings,
	discover_scenarios, load_settings, save_settings, selected_scenarios, validate_settings)

EVENT_PREFIX = 'BRS_BENCH_EVENT '
CHECKLIST = (
	'Локальные датчики', 'Датчики расширения', 'Удалённые датчики CAN',
	'Вход → выход программы', 'Сохранение привязок входов после питания',
	'Отвязка датчиков', 'Отвязка входа от выхода программы',
	'Сохранение отвязок входов после питания', 'Локальные реле',
	'Реле расширения', 'Удалённые реле CAN', 'Выход → вход программы',
	'Сохранение привязок выходов после питания', 'Отвязка локальных реле',
	'Отвязка реле расширения', 'Отвязка удалённых реле',
	'Отвязка выхода от входа программы', 'Сохранение отвязок выходов после питания',
	'Повторная привязка освобождённого реле',
)


class BenchFrame:
	def __init__(self, root):
		self.root = root
		root.title('Стенд 2.2 — HTTP/CAN привязки')
		root.geometry('1150x850')
		root.minsize(1000, 700)
		self.settings = default_settings()
		self.process = None
		self.run_directory = None
		self.closing = False
		self.stopping = False
		self.run_paths = []
		self.running_path = None
		self.events = queue.Queue()
		self.variables = {}
		self.editors = []
		self.actions = []
		self.scenarios = discover_scenarios()
		self.by_path = {item['path']: item for item in self.scenarios}
		self.status = tk.StringVar(value='Настройте выделенный стенд. PWM/0–10 V не проверяются.')
		self.notebook = ttk.Notebook(root)
		self.notebook.pack(fill='both', expand=True, padx=8, pady=8)
		self._build_connections()
		self.sensor_tree = self._build_table('Резисторные входы',
			('device', 'channel', 'expected', 'tolerance'),
			('Устройство', 'Вход S (с 1)', 'Температура, °C', 'Допуск, °C'), 'sensors')
		self.feedback_tree = self._build_table('Обратная связь реле',
			('output_device', 'relay', 'input_device', 'sensor', 'closed_when_on'),
			('Источник', 'Реле R (с 1)', 'Наблюдатель', 'Вход S (с 1)', 'КЗ при ON'), 'feedback')
		self._build_run()
		bar = ttk.Frame(root)
		bar.pack(fill='x', padx=8)
		for label, action in (('Сохранить', self.save), ('Проверить стенд', lambda: self.start(True)),
			('Запустить', lambda: self.start(False))):
			button = ttk.Button(bar, text=label, command=action)
			button.pack(side='left', padx=4)
			self.actions.append(button)
		self.stop_button = ttk.Button(bar, text='Остановить', command=self.stop, state='disabled')
		self.stop_button.pack(side='left', padx=4)
		ttk.Label(root, textvariable=self.status, wraplength=1100).pack(fill='x', padx=12, pady=8)
		self.console = tk.Text(root, height=9, state='disabled', wrap='word')
		self.console.pack(fill='both', padx=8, pady=(0, 8))
		try:
			self.settings = load_settings(SETTINGS_PATH)
		except FileNotFoundError:
			pass
		except (ValueError, OSError, UnicodeError) as error:
			messagebox.showerror('Настройки не загружены',
				f'{error}\nИсходный файл не изменён. Сохранение потребует подтверждения.', parent=root)
		self._restore()
		root.protocol('WM_DELETE_WINDOW', self.close)
		root.after(100, self.poll)

	def _entry(self, parent, row, label, key, choices=None, secret=False):
		ttk.Label(parent, text=label).grid(row=row, column=0, sticky='w', padx=6, pady=3)
		variable = tk.StringVar()
		self.variables[key] = variable
		if choices:
			widget = ttk.Combobox(parent, textvariable=variable, values=choices, state='readonly', width=32)
		else:
			widget = ttk.Entry(parent, textvariable=variable, width=35, show='*' if secret else '')
		widget.grid(row=row, column=1, sticky='ew', padx=6, pady=3)
		self.editors.append((widget, 'readonly' if choices else 'normal'))
		variable.trace_add('write', lambda *_: self.draw_topology())

	def _build_connections(self):
		page = ttk.Frame(self.notebook)
		self.notebook.add(page, text='Устройства и доступ')
		left = ttk.Frame(page)
		left.pack(side='left', fill='y')
		for row, role in enumerate(ROLES):
			self._entry(left, row, f'{LABELS[role]} — CAN ID', ('devices', role))
		self._entry(left, 4, 'Web URL (http://IP:порт)', ('web', 'url'))
		self._entry(left, 5, 'Логин', ('web', 'login'))
		self._entry(left, 6, 'Пароль', ('web', 'password'), secret=True)
		self._entry(left, 7, 'HTTP timeout, с', ('web', 'timeout'))
		self._entry(left, 8, 'Подключение', ('transport', 'mode'), ('can', 'udp'))
		self._entry(left, 9, 'CAN context из can.ini', ('transport', 'can_context'))
		self._entry(left, 10, 'UDP порт моста', ('transport', 'udp_port'))
		self._entry(left, 11, 'Служебное реле aux, R (с 1)', ('power', 'relay'))
		self._entry(left, 12, 'Команда отключения питания', ('power', 'off_value'), ('0', '255'))
		self._entry(left, 13, 'Время отключения, с', ('power', 'off_seconds'))
		self._entry(left, 14, 'Ожидание запуска, с', ('power', 'boot_timeout'))
		ttk.Label(left, text='Логин и пароль сохраняются открытым текстом.\n'
			'Питание aux-пары должно быть независимым.\n'
			'Управление питанием в этой версии НЕ выполняется.',
			wraplength=430).grid(row=15, column=0, columnspan=2, padx=6, pady=12)
		diagram = ttk.Frame(page)
		diagram.pack(side='right', fill='both', expand=True, padx=8, pady=8)
		self.canvas = tk.Canvas(diagram, background='white', highlightthickness=0)
		scrollbar = ttk.Scrollbar(diagram, orient='vertical', command=self.canvas.yview)
		self.canvas.configure(yscrollcommand=scrollbar.set)
		scrollbar.pack(side='right', fill='y')
		self.canvas.pack(side='left', fill='both', expand=True)
		self.canvas.bind('<Configure>', lambda _: self.draw_topology())

	def _build_table(self, title, columns, headings, key):
		page = ttk.Frame(self.notebook)
		self.notebook.add(page, text=title)
		tree = ttk.Treeview(page, columns=columns, show='headings', selectmode='browse')
		for column, heading in zip(columns, headings):
			tree.heading(column, text=heading)
			tree.column(column, width=150, stretch=True)
		tree.pack(fill='both', expand=True, padx=8, pady=8)
		bar = ttk.Frame(page)
		bar.pack(fill='x', padx=8, pady=8)
		for label, action in (('Добавить', lambda: self.edit_row(key, tree)),
			('Изменить', lambda: self.edit_row(key, tree, True)),
			('Удалить', lambda: self.remove_row(key, tree))):
			button = ttk.Button(bar, text=label, command=action)
			button.pack(side='left', padx=4)
			self.actions.append(button)
		ttk.Label(page, text='Все номера каналов начинаются с 1. Связи задаются явно; совпадение Rn → Sn не предполагается.').pack(pady=8)
		return tree

	def _build_run(self):
		page = ttk.Frame(self.notebook)
		self.notebook.add(page, text='Сценарии')
		ttk.Label(page, text='Ctrl/Shift — выбор нескольких. 9.1.1/9.1.2 — существующие проверки только привязок; не полное покрытие 2.2.',
			wraplength=1000).pack(pady=8)
		self.scenario_tree = ttk.Treeview(page, columns=('id', 'title', 'result'), show='headings', selectmode='extended')
		for column, heading, width in (('id', 'Пункт', 90), ('title', 'Сценарий', 650), ('result', 'Результат / доступность', 220)):
			self.scenario_tree.heading(column, text=heading)
			self.scenario_tree.column(column, width=width)
		self.scenario_tree.pack(fill='both', expand=True, padx=8, pady=8)
		implemented = {item['id'] for item in self.scenarios}
		for index, title in enumerate(CHECKLIST, 1):
			checklist_id = f'2.2.{index}'
			if checklist_id not in implemented:
				self.scenario_tree.insert('', 'end', iid=f'missing:{checklist_id}', values=(checklist_id, title, 'Не реализован'))
		for item in self.scenarios:
			self.scenario_tree.insert('', 'end', iid=item['path'], values=(item['id'], item['title'], 'Не запускался'))

	def _restore(self):
		for (section, key), variable in self.variables.items():
			variable.set(str(self.settings[section][key]))
		for tree, key in ((self.sensor_tree, 'sensors'), (self.feedback_tree, 'feedback')):
			self._refresh_table(key, tree)
		self.scenario_tree.selection_set([path for path in self.settings['scenarios'] if path in self.by_path])
		self.draw_topology()

	def collect(self):
		settings = copy.deepcopy(self.settings)
		for (section, key), variable in self.variables.items():
			value = variable.get()
			old = settings[section][key]
			if type(old) is int:
				value = float(value) if key in ('timeout', 'off_seconds', 'boot_timeout') else int(value)
			elif type(old) is float:
				value = float(value)
			settings[section][key] = value
		settings['scenarios'] = [path for path in self.scenario_tree.selection() if path in self.by_path]
		return validate_settings(settings)

	def save(self):
		if self.process:
			return False
		try:
			settings = self.collect()
			if SETTINGS_PATH.exists():
				try:
					load_settings(SETTINGS_PATH)
				except (ValueError, OSError, UnicodeError):
					if not messagebox.askyesno('Заменить повреждённый профиль?', 'Исходный файл настроек будет заменён.', parent=self.root):
						return False
			save_settings(settings, SETTINGS_PATH)
			self.settings = settings
			self.status.set(f'Сохранено: {SETTINGS_PATH.name} (пароль — открытым текстом)')
			return True
		except (ValueError, OSError) as error:
			messagebox.showerror('Настройки', str(error), parent=self.root)
			return False

	def _refresh_table(self, key, tree):
		tree.delete(*tree.get_children())
		columns = tree['columns']
		for index, row in enumerate(self.settings[key]):
			tree.insert('', 'end', iid=str(index), values=[row[column] for column in columns])
		self.draw_topology()

	def remove_row(self, key, tree):
		if not self.process and tree.selection():
			del self.settings[key][int(tree.selection()[0])]
			self._refresh_table(key, tree)

	def edit_row(self, key, tree, existing=False):
		if self.process or (existing and not tree.selection()):
			return
		index = int(tree.selection()[0]) if existing else None
		row = self.settings[key][index] if existing else (
			{'device': 'dut_controller', 'channel': 1, 'expected': 20.0, 'tolerance': 2.0} if key == 'sensors' else
			{'output_device': 'dut_controller', 'relay': 1, 'input_device': 'aux_controller', 'sensor': 1, 'closed_when_on': True})
		dialog = tk.Toplevel(self.root)
		dialog.title('Канал стенда')
		dialog.transient(self.root)
		dialog.grab_set()
		variables = {}
		for number, (name, value) in enumerate(row.items()):
			ttk.Label(dialog, text=tree.heading(name)['text']).grid(row=number, column=0, padx=8, pady=5)
			var = tk.StringVar(value=str(value))
			variables[name] = var
			choices = ROLES if name.endswith('device') else ('True', 'False') if name == 'closed_when_on' else None
			widget = ttk.Combobox(dialog, textvariable=var, values=choices, state='readonly') if choices else ttk.Entry(dialog, textvariable=var)
			widget.grid(row=number, column=1, padx=8, pady=5)
		def accept():
			try:
				updated = {name: (var.get() == 'True' if name == 'closed_when_on' else
					int(var.get()) if name in ('channel', 'relay', 'sensor') else
					float(var.get()) if name in ('expected', 'tolerance') else var.get())
					for name, var in variables.items()}
				settings = self.collect()
				if index is None:
					settings[key].append(updated)
				else:
					settings[key][index] = updated
				validate_settings(settings)
				self.settings = settings
				self._refresh_table(key, tree)
				dialog.destroy()
			except ValueError as error:
				messagebox.showerror('Канал', str(error), parent=dialog)
		ttk.Button(dialog, text='OK', command=accept).grid(row=len(row), column=1, pady=8)

	def draw_topology(self):
		if not hasattr(self, 'canvas'):
			return
		canvas = self.canvas
		canvas.delete('all')
		width = max(canvas.winfo_width(), 430)
		centres = {'dut_controller': (width * .26, 95), 'aux_controller': (width * .74, 95),
			'dut_extension': (width * .26, 235), 'aux_extension': (width * .74, 235)}
		for role, (x, y) in centres.items():
			canvas.create_rectangle(x-95, y-35, x+95, y+35, fill='#e7f0fa', outline='#416080', width=2)
			value = self.variables.get(('devices', role))
			canvas.create_text(x, y, text=f'{LABELS[role]}\nCAN ID: {value.get() if value else "?"}', width=185)
		canvas.create_line(centres['dut_controller'][0]+95, 95, centres['aux_controller'][0]-95, 95)
		canvas.create_text(width*.5, 75, text='CAN')
		for role in ('dut_controller', 'aux_controller'):
			x = centres[role][0]
			canvas.create_line(x, 130, x, 200)
			canvas.create_text(x+20, 165, text='I²C')
		for source, observer, y in (('dut_controller', 'aux_controller', 140),
			('dut_extension', 'aux_extension', 285)):
			if any(row['output_device'] == source and row['input_device'] == observer
					for row in self.settings['feedback']):
				x1, x2 = centres[source][0], centres[observer][0]
				canvas.create_line(x1, y-10, x1, y, x2, y, x2, y-10,
					arrow=tk.LAST, fill='#248140', dash=(4, 2))
		canvas.create_line(centres['aux_controller'][0], 60, centres['aux_controller'][0], 28,
			centres['dut_controller'][0], 28, centres['dut_controller'][0], 60,
			arrow=tk.LAST, fill='#9a4400')
		canvas.create_text(width*.5, 15, text='Управление питанием', fill='#9a4400')
		y = 310
		canvas.create_text(12, y, anchor='nw', text='Обратные связи (контакты → измерительные входы):')
		for row in self.settings['feedback']:
			y += 24
			canvas.create_text(12, y, anchor='nw', text=f'{row["output_device"]} R{row["relay"]} → {row["input_device"]} S{row["sensor"]}')
		y += 36
		relay = self.variables.get(('power', 'relay'))
		canvas.create_text(12, y, anchor='nw', width=width-24, fill='#9a4400',
			text=f'Питание: aux R{relay.get() if relay else "?"} → SWK + его SWK_1\nВспомогательная пара питается независимо.')
		canvas.configure(scrollregion=(0, 0, width, max(y+70, canvas.winfo_height())))

	def start(self, check_only):
		if self.process:
			return
		try:
			settings = self.collect()
			validate_settings(settings, require_ready=True)
			if not check_only:
				if any(path.startswith('missing:') for path in self.scenario_tree.selection()):
					raise ValueError('Выбраны нереализованные пункты. Выберите только доступные сценарии.')
				selected_scenarios(settings)
				if not messagebox.askyesno('Выделенный стенд',
					f'Подтвердите выделенный стенд без реальных нагрузок.\n'
					f'Программы тестируемого SWK (ID {settings["devices"]["dut_controller"]}) будут удалены.\n'
					'Восстановления исходной конфигурации нет.\nПродолжить?', parent=self.root):
					return
			if not self.save():
				return
			self.run_directory = tempfile.TemporaryDirectory(prefix='brs_bench_')
			snapshot = Path(self.run_directory.name) / 'profile.json'
			save_settings(settings, snapshot)
			command = [sys.executable, '-u', str(ROOT / 'web_binding_bench_runner.py'),
				'--profile', str(snapshot), '--check' if check_only else '--run']
			if not check_only:
				command.append('--confirm-bench')
			self.process = subprocess.Popen(command, cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
				stderr=subprocess.STDOUT, text=True, encoding='utf-8', errors='replace',
				creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
			self.stopping = False
			self.run_paths = [] if check_only else list(settings['scenarios'])
			self.running_path = None
			for button in self.actions:
				button.configure(state='disabled')
			for widget, _ in self.editors:
				widget.configure(state='disabled')
			self.stop_button.configure(state='normal')
			self.scenario_tree.configure(selectmode='none')
			self.status.set('Проверка доступности стенда…' if check_only else 'Прогон стенда…')
			for path in self.run_paths:
				self.scenario_tree.set(path, 'result', 'Не запускался')
			threading.Thread(target=self._read_process, args=(self.process,), daemon=True).start()
		except (ValueError, OSError) as error:
			if self.run_directory:
				self.run_directory.cleanup()
				self.run_directory = None
			messagebox.showerror('Запуск', str(error), parent=self.root)

	def _read_process(self, process):
		for line in process.stdout:
			self.events.put(line)
		process.wait()
		self.events.put(('exit', process.returncode))

	def log(self, text):
		self.console.configure(state='normal')
		self.console.insert('end', text)
		if int(self.console.index('end-1c').split('.')[0]) > 2000:
			self.console.delete('1.0', '200.0')
		self.console.see('end')
		self.console.configure(state='disabled')

	def poll(self):
		for _ in range(100):
			try:
				item = self.events.get_nowait()
			except queue.Empty:
				break
			if isinstance(item, tuple):
				self.status.set(f'Процесс завершён, код {item[1]}.' + (' Остановлено.' if self.stopping else ''))
				self.log(self.status.get() + '\n')
				if self.running_path and self.scenario_tree.set(self.running_path, 'result') == 'Выполняется':
					self.scenario_tree.set(self.running_path, 'result', 'Прерван' if self.stopping else 'Ошибка процесса')
				for stream in (self.process.stdin, self.process.stdout):
					stream.close()
				self.process = None
				self.run_directory.cleanup()
				self.run_directory = None
				for button in self.actions:
					button.configure(state='normal')
				for widget, state in self.editors:
					widget.configure(state=state)
				self.stop_button.configure(state='disabled')
				self.scenario_tree.configure(selectmode='extended')
				if self.closing:
					self.root.destroy()
					return
			elif item.startswith(EVENT_PREFIX):
				try:
					data = json.loads(item[len(EVENT_PREFIX):])
					self.status.set(data.get('message', data.get('event', '')))
					self.log(self.status.get() + '\n')
					if data.get('event') == 'progress' and data.get('path') in self.run_paths:
						self.running_path = data['path']
						self.scenario_tree.set(self.running_path, 'result', 'Выполняется')
					if data.get('event') == 'result':
						self.log(f'{data.get("checklistId")}: {data.get("result")}\n')
						for path, scenario in self.by_path.items():
							if scenario['id'] == data.get('checklistId'):
								self.scenario_tree.set(path, 'result', data['result'])
				except (ValueError, KeyError):
					self.log('Некорректное сообщение рабочего процесса.\n')
			else:
				self.log(item)
		self.root.after(100, self.poll)

	def stop(self):
		if self.process and not self.stopping:
			self.stopping = True
			self.status.set('Остановка и очистка; дождитесь завершения процесса…')
			try:
				self.process.stdin.write('stop\n')
				self.process.stdin.flush()
			except (OSError, ValueError):
				pass
			self.stop_button.configure(state='disabled')

	def close(self):
		if self.process:
			if messagebox.askyesno('Закрыть', 'Остановить проверку и дождаться очистки?', parent=self.root):
				self.closing = True
				self.stop()
		elif messagebox.askyesno('Закрыть', 'Сохранить настройки перед закрытием?', parent=self.root):
			if self.save():
				self.root.destroy()
		else:
			self.root.destroy()


def main():
	root = tk.Tk()
	BenchFrame(root)
	root.mainloop()