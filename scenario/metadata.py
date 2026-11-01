"""Scenario estimates and metadata that can be read without importing scenarios.

Estimates are typical successful run times in seconds, excluding preset loading.
They are deliberately approximate: controller response and physical models vary.
Revisit the relevant estimate whenever a scenario's timing or sequence changes.
"""

import ast
from pathlib import Path


PRESET_LOADING_ESTIMATE_SECONDS = 10

# Estimates are keyed by the exact, externally visible checklist ID. In
# particular, 3.11.7 & 3.11.9 is one combined scenario, not two executions.
SCENARIO_RUN_ESTIMATES = {
	# Rooms: schedule-based cases also wait for the real controller clock.
	'3.2.2': 480, '3.2.3': 120, '3.2.4': 90,
	# Heating-circuit demand, mixer, line and alarm checks.
	'3.3.2': 360, '3.3.3': 300, '3.3.4': 360,
	'3.3.5.1': 600, '3.3.5.2': 600, '3.3.5.3': 600,
	'3.3.6': 600, '3.3.7': 600, '3.3.11': 240,
	# DHW and boiler.
	'3.4.1': 60, '3.4.2': 90, '3.4.3': 90, '3.4.4': 90, '3.4.6': 180,
	'3.5.2': 90, '3.5.3': 240, '3.5.4': 60, '3.5.6': 300, '3.5.7': 600,
	# Cascade stage sequences: delayed stages and fault replacements take longer
	# as the number of boilers increases.
	'3.6.3': 120, '3.6.3.1': 120, '3.6.3.2': 150, '3.6.3.3': 180,
	'3.6.3.4': 360, '3.6.3.5': 420, '3.6.3.6': 480,
	'3.6.3.7': 240, '3.6.3.8': 360, '3.6.3.9': 480,
	'3.6.3.10': 420, '3.6.3.11': 600, '3.6.3.12': 840, '3.6.4': 90,
	# Snowmelter: 3.9.3 tests both limits with two five-minute delays and holds.
	'3.9.1': 420, '3.9.2': 420, '3.9.3': 1320, '3.9.4': 900, '3.9.5': 480,
	'3.10.1': 600,
	# Pool 3.11.2 includes six five-minute holds and three three-minute cycles.
	'3.11.1': 90, '3.11.2': 2580, '3.11.3': 90, '3.11.4': 90,
	'3.11.6': 90, '3.11.7 & 3.11.9': 180, '3.11.8': 90,
	# District heating: periodic valve opening occurs once every three hours.
	'3.12.1': 60, '3.12.2': 360, '3.12.3': 420, '3.12.4': 420,
	'3.12.5': 210, '3.12.6': 900, '3.12.7': 360, '3.12.8': 11400,
	'3.12.9': 600, '3.12.10.1': 120, '3.12.10.2': 11400,
	'3.12.10.3': 240, '3.12.10.4': 180, '3.12.10.5': 600,
	'3.12.10.6': 300, '3.12.11': 120,
	'3.13.1': 60, '3.13.2': 60, '3.13.3': 60,
	'3.13.4': 60, '3.13.5': 90, '3.13.6': 90,
	# Priority checks. DHW cold-fault suppression waits for the real one-hour delay.
	'5.1.1.1': 120, '5.1.1.2': 120, '5.1.1.3': 3900,
	'5.1.2.1': 90, '5.1.3.1': 180, '5.1.3.2': 180,
	'5.2.1.1': 90,
	'5.2.2.1': 120, '5.2.2.2': 120, '5.2.2.3': 150,
	'5.2.2.4': 120, '5.2.2.5': 120, '5.2.2.6': 150,
	'5.2.3.1': 240, '5.2.3.2': 240, '5.2.3.3': 180, '5.2.4.1': 90,
	# Heat dump checks.
	'6.1.1': 60, '6.2.1': 60, '6.2.2': 60, '6.3.1': 60, '6.3.2': 60,
	'6.4.1': 60, '6.4.2': 120, '6.5.1': 90, '6.5.2': 120,
	# 9.5 observes the complete, real one-hour disinfection cycle.
	'9.1': 90, '9.2': 120, '9.3': 90, '9.4': 180, '9.5': 3900,
	'9.6': 180, '9.7': 240, '9.9': 90, '9.10': 120,
	'9.11': 90, '9.12': 120, '9.13': 90, '9.28': 120,
	'9.29': 120, '9.30': 150, '9.32': 90,
}


def get_estimated_duration(checklist_id):
	"""Return estimated seconds including preset loading, or None if unknown."""
	duration = SCENARIO_RUN_ESTIMATES.get(checklist_id)
	return None if duration is None else duration + PRESET_LOADING_ESTIMATE_SECONDS


def format_estimated_duration(seconds):
	"""Format an approximate duration without hiding the preset allowance."""
	if seconds is None:
		return 'время неизвестно'
	hours, remainder = divmod(seconds, 3600)
	minutes, seconds = divmod(remainder, 60)
	parts = []
	if hours:
		parts.append(f'{hours} ч')
	if minutes:
		parts.append(f'{minutes} мин')
	if seconds:
		parts.append(f'{seconds} с')
	return '≈ ' + ' '.join(parts or ['0 с'])


def read_scenario_metadata(path):
	"""Read literal title and ID from source, without importing or constructing it.

	A broken, missing, or dynamically defined scenario remains selectable by path;
	in that case its unavailable metadata is left unknown.
	"""
	try:
		with open(path, encoding='utf-8-sig') as source:
			tree = ast.parse(source.read(), filename=str(path))
	except (OSError, UnicodeError, SyntaxError, ValueError):
		return None, None
	for node in tree.body:
		if isinstance(node, ast.ClassDef) and node.name == 'Scenario':
			values = {}
			for method in node.body:
				if (isinstance(method, ast.FunctionDef)
						and method.name in ('get_scenario_title', 'get_checklist_id')
						and len(method.body) == 1 and isinstance(method.body[0], ast.Return)):
					value = method.body[0].value
					if isinstance(value, ast.Constant) and isinstance(value.value, str):
						values[method.name] = value.value
			return values.get('get_scenario_title'), values.get('get_checklist_id')
	return None, None


def scenario_label(path, include_path=False, scenario_dir=None):
	"""Build a label while preserving the original path as the selection value."""
	title, checklist_id = read_scenario_metadata(path)
	name = title or Path(path).name
	if checklist_id:
		name = f'{checklist_id}: {name}'
	label = f'{name} ({format_estimated_duration(get_estimated_duration(checklist_id))})'
	if include_path and scenario_dir is not None:
		try:
			relative_path = Path(path).relative_to(scenario_dir).as_posix()
		except ValueError:
			relative_path = str(path)
		label += f' — {relative_path}'
	return label