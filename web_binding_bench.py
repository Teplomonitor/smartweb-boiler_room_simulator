"""Physical bench configuration. Channel numbers in this file are one-based."""

import copy
import json
import math
import os
from pathlib import Path
import tempfile

ROOT = Path(__file__).resolve().parent
SETTINGS_PATH = ROOT / 'web_binding_bench_settings.json'
ROLES = ('dut_controller', 'dut_extension', 'aux_controller', 'aux_extension')
LABELS = dict(zip(ROLES, ('Тестируемый SWK', 'Тестируемый SWK_1',
	'Вспомогательный контроллер', 'Вспомогательный SWK_1')))
PARENTS = {'dut_extension': 'dut_controller', 'aux_extension': 'aux_controller'}


def default_settings():
	return {
		'version': 1,
		'devices': {role: 0 for role in ROLES},
		'web': {'url': '', 'login': 'admin', 'password': 'admin', 'timeout': 10},
		'transport': {'mode': 'udp', 'can_context': 'virtual', 'udp_port': 31987},
		'sensors': [],
		'feedback': [],
		'power': {'device': 'aux_controller', 'relay': 0, 'off_value': 255,
			'off_seconds': 5, 'boot_timeout': 120},
		'scenarios': [],
	}


def _integer(value, low, high, name):
	if type(value) is not int or not low <= value <= high:
		raise ValueError(f'{name}: ожидается целое число {low}..{high}')


def _number(value, low, high, name):
	if type(value) not in (int, float) or not math.isfinite(value) or not low <= value <= high:
		raise ValueError(f'{name}: ожидается число {low}..{high}')


def _channel(row, device_key, channel_key):
	if row.get(device_key) not in ROLES:
		raise ValueError(f'{device_key}: неизвестное устройство')
	_integer(row.get(channel_key), 1, 32, channel_key)
	return row[device_key], row[channel_key]


def validate_settings(settings, require_ready=False):
	"""Validate drafts too; a runnable profile additionally needs all wiring and IDs."""
	if not isinstance(settings, dict) or type(settings.get('version')) is not int or settings['version'] != 1:
		raise ValueError('Неподдерживаемая версия профиля стенда')
	devices = settings.get('devices')
	if not isinstance(devices, dict) or set(devices) != set(ROLES):
		raise ValueError('Нужно задать четыре устройства стенда')
	for role, value in devices.items():
		_integer(value, 1 if require_ready else 0, 255, LABELS[role])
	assigned = [value for value in devices.values() if value]
	if len(assigned) != len(set(assigned)):
		raise ValueError('CAN ID устройств должны быть различны')
	for extension, parent in PARENTS.items():
		if devices[extension] and devices[parent] and devices[extension] != devices[parent] % 255 + 1:
			raise ValueError(f'{LABELS[extension]}: ожидается ID головного контроллера + 1 (после 255 — 1)')
	web = settings.get('web')
	if not isinstance(web, dict) or any(not isinstance(web.get(key), str) for key in ('url', 'login', 'password')):
		raise ValueError('Неверные настройки HTTP')
	_number(web.get('timeout'), 0.1, 300, 'HTTP timeout')
	if web['url'] or require_ready:
		from webapi.client import ControllerWebClient
		ControllerWebClient(web['url'], timeout=web['timeout'])
	transport = settings.get('transport')
	if not isinstance(transport, dict) or transport.get('mode') not in ('can', 'udp'):
		raise ValueError('Выберите CAN или UDP')
	if not isinstance(transport.get('can_context'), str):
		raise ValueError('Неверное имя CAN-конфигурации')
	_integer(transport.get('udp_port'), 1, 65535, 'UDP port')
	if require_ready and transport['mode'] == 'can' and transport['can_context'] in ('', 'none', 'virtual'):
		raise ValueError('Укажите аппаратную CAN-конфигурацию')
	power = settings.get('power')
	if not isinstance(power, dict) or power.get('device') != 'aux_controller':
		raise ValueError('Реле питания должно принадлежать вспомогательному контроллеру')
	_integer(power.get('relay'), 1 if require_ready else 0, 32, 'Реле питания')
	if type(power.get('off_value')) is not int or power['off_value'] not in (0, 255):
		raise ValueError('Команда отключения питания: только 0 или 255')
	_number(power.get('off_seconds'), 1, 60, 'Время отключения')
	_number(power.get('boot_timeout'), 10, 600, 'Ожидание запуска')
	sensors, feedback = settings.get('sensors'), settings.get('feedback')
	if not isinstance(sensors, list) or not isinstance(feedback, list):
		raise ValueError('Датчики и обратные связи должны быть списками')
	inputs, outputs = set(), set()
	for row in sensors:
		if not isinstance(row, dict):
			raise ValueError('Неверная строка датчика')
		key = _channel(row, 'device', 'channel')
		if key in inputs:
			raise ValueError('Вход датчика указан повторно')
		inputs.add(key)
		_number(row.get('expected'), -100, 300, 'Ожидаемая температура, °C')
		_number(row.get('tolerance'), 0.1, 50, 'Допуск, °C')
	for row in feedback:
		if not isinstance(row, dict):
			raise ValueError('Неверная строка обратной связи')
		output = _channel(row, 'output_device', 'relay')
		observer = _channel(row, 'input_device', 'sensor')
		if output == (power['device'], power['relay']):
			raise ValueError('Служебное реле питания нельзя тестировать')
		if output in outputs or observer in inputs:
			raise ValueError('Повторное использование реле или измерительного входа')
		if row.get('closed_when_on') is not True and row.get('closed_when_on') is not False:
			raise ValueError('Укажите полярность контакта')
		outputs.add(output)
		inputs.add(observer)
	if require_ready:
		for role in ('dut_controller', 'dut_extension'):
			if not any(row['device'] == role for row in sensors):
				raise ValueError(f'{LABELS[role]}: нужен хотя бы один резисторный вход')
			if not any(row['output_device'] == role for row in feedback):
				raise ValueError(f'{LABELS[role]}: нужна хотя бы одна обратная связь реле')
	if not isinstance(settings.get('scenarios'), list) or any(not isinstance(item, str) for item in settings['scenarios']):
		raise ValueError('Неверный список сценариев')
	return settings


def load_settings(path=SETTINGS_PATH):
	with Path(path).open(encoding='utf-8') as stream:
		return validate_settings(json.load(stream))


def save_settings(settings, path=SETTINGS_PATH):
	validate_settings(settings)
	path = Path(path)
	temp_path = None
	try:
		with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
			prefix=f'.{path.name}.', suffix='.tmp', delete=False) as stream:
			temp_path = Path(stream.name)
			json.dump(settings, stream, ensure_ascii=False, indent=2)
			stream.write('\n')
		os.replace(temp_path, path)
	finally:
		if temp_path is not None:
			temp_path.unlink(missing_ok=True)


def discover_scenarios():
	"""Read metadata without importing CAN, wx, application or scenario classes."""
	from scenario.metadata import read_scenario_details
	items = []
	for path in (ROOT / 'scenario' / 'list').rglob('*.py'):
		title, checklist_id, _ = read_scenario_details(path)
		if checklist_id and (checklist_id.startswith('2.2.') or checklist_id in ('9.1.1', '9.1.2')):
			items.append({'id': checklist_id, 'title': title or path.stem,
				'path': path.relative_to(ROOT).as_posix()})
	return sorted(items, key=lambda item: tuple(int(part) for part in item['id'].split('.')))


def selected_scenarios(settings):
	available = {item['path']: item for item in discover_scenarios()}
	if not settings['scenarios']:
		raise ValueError('Выберите хотя бы один реализованный сценарий')
	if len(set(settings['scenarios'])) != len(settings['scenarios']):
		raise ValueError('Сценарий выбран повторно')
	if any(path not in available for path in settings['scenarios']):
		raise ValueError('Выбран отсутствующий или посторонний сценарий; выберите список заново')
	return [str(ROOT / path) for path in settings['scenarios']]


def required_channels(settings):
	counts = {role: [0, 0] for role in ROLES}
	for row in settings['sensors']:
		counts[row['device']][0] = max(counts[row['device']][0], row['channel'])
	for row in settings['feedback']:
		counts[row['input_device']][0] = max(counts[row['input_device']][0], row['sensor'])
		counts[row['output_device']][1] = max(counts[row['output_device']][1], row['relay'])
	counts['aux_controller'][1] = max(counts['aux_controller'][1], settings['power']['relay'])
	return counts


def preflight(settings, can_client, web_client, log=print, cancelled=lambda: False):
	"""Read-only discovery. Does not exercise wiring, switch power or load presets."""
	validate_settings(settings, require_ready=True)
	from smartnet.constants import ControllerType
	needed = required_channels(settings)
	for role in ROLES:
		if cancelled():
			raise RuntimeError('Проверка стенда отменена')
		controller_id = settings['devices'][role]
		controller_type = can_client.read_controller_type(controller_id)
		counts = can_client.read_channel_counts(controller_id)
		if len(counts) != 2 or any(type(count) is not int or not 0 <= count <= 32 for count in counts):
			raise ValueError(f'{role}: неверное число каналов')
		if role in PARENTS and controller_type != int(ControllerType['SWK_1']):
			raise ValueError(f'{role}: CAN ID {controller_id} не объявлен как SWK_1')
		if any(have < minimum for have, minimum in zip(counts, needed[role])):
			raise ValueError(f'{role}: недостаточно каналов для указанной разводки')
		log(f'{LABELS[role]}: CAN ID={controller_id}, тип={controller_type}, S={counts[0]}, R={counts[1]}')
	try:
		web_client.login()
		config = web_client.config()
		for role, controller_id in settings['devices'].items():
			matches = [item for item in config['controllers'] if item.get('id') == controller_id]
			if len(matches) != 1:
				raise ValueError(f'{LABELS[role]}: устройство не видно однозначно через HTTP')
	finally:
		web_client.logout()
	log('HTTP/CAN: все четыре узла доступны. Физическая разводка и реле питания НЕ проверялись.')
	return copy.deepcopy(settings)