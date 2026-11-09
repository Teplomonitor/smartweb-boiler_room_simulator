"""GUI connection settings; no GUI, transport or hardware imports."""

import configparser
import json
from pathlib import Path


DEFAULT_SETTINGS = {
	'controller_id': 0,
	'transport': 'can',
	'can_context': 'default',
	'udp_port': 31987,
}


def can_contexts():
	parser = configparser.ConfigParser(interpolation=None)
	parser.read(Path(__file__).resolve().parent / 'can.ini', encoding='utf-8')
	return parser.sections()


def validate_settings(settings):
	result = dict(DEFAULT_SETTINGS, **settings)
	try:
		result['controller_id'] = int(str(result['controller_id']))
		result['udp_port'] = int(str(result['udp_port']))
	except (TypeError, ValueError) as exc:
		raise ValueError('ID и UDP-порт должны быть целыми числами.') from exc
	if not 0 <= result['controller_id'] <= 255:
		raise ValueError('ID контроллера: 0–255 (0 — автопоиск).')
	if not 1 <= result['udp_port'] <= 65535:
		raise ValueError('UDP-порт: 1–65535.')
	if result['transport'] not in ('can', 'udp'):
		raise ValueError('Выберите CAN или UDP.')
	if not isinstance(result['can_context'], str) or not result['can_context'].strip():
		raise ValueError('Выберите конфигурацию CAN.')
	return {key: result[key] for key in DEFAULT_SETTINGS}


def load_settings(config, profile):
	try:
		value = json.loads(config.getParameterValue(profile, 'connection_settings'))
		if not isinstance(value, dict):
			return dict(DEFAULT_SETTINGS)
		return validate_settings(value)
	except (configparser.Error, ValueError, TypeError):
		return dict(DEFAULT_SETTINGS)


def save_settings(config, profile, settings):
	settings = validate_settings(settings)
	config.setParameterValue(profile, 'connection_settings', json.dumps(settings))
	return settings
