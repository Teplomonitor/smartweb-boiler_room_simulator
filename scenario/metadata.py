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
# Measured estimates use the median successful scenario duration from the
# available parallel-run results, plus 20%, rounded up to 10 seconds. Most
# scenarios have only one measurement; unmeasured estimates are unchanged.
SCENARIO_RUN_ESTIMATES = {
	# Rooms: schedule-based cases also wait for the real controller clock.
	'3.2.2': 530, '3.2.3': 120, '3.2.4': 110,
	# Heating-circuit demand, mixer, line and alarm checks.
	'3.3.2': 610, '3.3.3': 1300, '3.3.4': 160,
	'3.3.5.1': 400, '3.3.5.2': 880, '3.3.5.3': 1180,
	'3.3.6': 2610, '3.3.7': 2270, '3.3.11': 140,
	# DHW and boiler.
	'3.4.1': 10, '3.4.2': 90, '3.4.3': 20, '3.4.4': 10, '3.4.6': 50,
	'3.5.2': 80, '3.5.3': 160, '3.5.4': 730, '3.5.6': 60, '3.5.7': 610,
	# Cascade stage sequences: delayed stages and fault replacements take longer
	# as the number of boilers increases.
	'3.6.3': 300, '3.6.3.1': 260, '3.6.3.2': 340, '3.6.3.3': 180,
	'3.6.3.4': 550, '3.6.3.5': 420, '3.6.3.6': 780,
	'3.6.3.7': 1130, '3.6.3.8': 360, '3.6.3.9': 480,
	'3.6.3.10': 420, '3.6.3.11': 600, '3.6.3.12': 840, '3.6.4': 50,
	# Snowmelter: 3.9.3 tests both limits with two five-minute delays and holds.
	'3.9.1': 420, '3.9.2': 410, '3.9.3': 1470, '3.9.4': 780, '3.9.5': 480,
	'3.10.1': 580,
	# Pool 3.11.2 includes six five-minute holds and three three-minute cycles.
	'3.11.1': 10, '3.11.2': 2580, '3.11.3': 70, '3.11.4': 20,
	'3.11.6': 50, '3.11.7 & 3.11.9': 480, '3.11.8': 80,
	# District heating: periodic valve opening occurs once every three hours.
	'3.12.1': 30, '3.12.2': 1060, '3.12.3': 420, '3.12.4': 440,
	'3.12.5': 190, '3.12.6': 910, '3.12.7': 280, '3.12.8': 11400,
	'3.12.9': 500, '3.12.10.1': 120, '3.12.10.2': 11400,
	'3.12.10.3': 210, '3.12.10.4': 180, '3.12.10.5': 600,
	'3.12.10.6': 540, '3.12.11': 120,
	'3.13.1': 40, '3.13.2': 60, '3.13.3': 120,
	'3.13.4': 60, '3.13.5': 60, '3.13.6': 30,
	# Priority checks. DHW cold-fault suppression waits for the real one-hour delay.
	'5.1.1.1': 40, '5.1.1.2': 20, '5.1.1.3': 3900,
	'5.1.2.1': 60, '5.1.3.1': 390, '5.1.3.2': 420,
	'5.2.1.1': 30,
	'5.2.2.1': 30, '5.2.2.2': 30, '5.2.2.3': 40,
	'5.2.2.4': 30, '5.2.2.5': 30, '5.2.2.6': 40,
	'5.2.3.1': 290, '5.2.3.2': 280, '5.2.3.3': 220, '5.2.4.1': 40,
	# Heat dump checks.
	'6.1.1': 50, '6.2.1': 60, '6.2.2': 20, '6.3.1': 30, '6.3.2': 30,
	'6.4.1': 110, '6.4.2': 120, '6.5.1': 80, '6.5.2': 150,
	# 9.5 observes the complete, real one-hour disinfection cycle.
	'9.1': 40, '9.2': 70, '9.3': 10, '9.4': 160, '9.5': 3900,
	'9.6': 80, '9.7': 110, '9.9': 40, '9.10': 40,
	'9.11': 30, '9.12': 40, '9.13': 20, '9.28': 100,
	'9.29': 40, '9.30': 70, '9.32': 30,
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