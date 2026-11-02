"""Scenario estimates and metadata that can be read without importing scenarios.

Estimates are typical successful run times in seconds, excluding preset loading.
They are deliberately approximate: controller response and physical models vary.
Revisit the relevant estimate whenever a scenario's timing or sequence changes.
Measured estimates use the median successful duration plus 20%, rounded up to
10 seconds. Most scenarios have only one measurement; unmeasured estimates
retain the original approximate values.
"""

import ast
from pathlib import Path


PRESET_LOADING_ESTIMATE_SECONDS = 10

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


def read_scenario_details(path):
	"""Read literal title, ID and run estimate without importing the scenario.

	A broken, missing, or dynamically defined scenario remains selectable by path;
	in that case its unavailable metadata is left unknown.
	"""
	try:
		with open(path, encoding='utf-8-sig') as source:
			tree = ast.parse(source.read(), filename=str(path))
	except (OSError, UnicodeError, SyntaxError, ValueError):
		return None, None, None
	for node in tree.body:
		if isinstance(node, ast.ClassDef) and node.name == 'Scenario':
			values = {}
			estimate = None
			for method in node.body:
				if (isinstance(method, ast.Assign) and len(method.targets) == 1
						and isinstance(method.targets[0], ast.Name)
						and method.targets[0].id == 'ESTIMATED_RUN_SECONDS'
						and isinstance(method.value, ast.Constant)
						and type(method.value.value) is int and method.value.value > 0):
					estimate = method.value.value
				if (isinstance(method, ast.FunctionDef)
						and method.name in ('get_scenario_title', 'get_checklist_id')
						and len(method.body) == 1 and isinstance(method.body[0], ast.Return)):
					value = method.body[0].value
					if isinstance(value, ast.Constant) and isinstance(value.value, str):
						values[method.name] = value.value
			return values.get('get_scenario_title'), values.get('get_checklist_id'), estimate
	return None, None, None


def read_scenario_metadata(path):
	"""Return the title and ID, preserving the existing two-value API."""
	title, checklist_id, _ = read_scenario_details(path)
	return title, checklist_id


def scenario_label(path, include_path=False, scenario_dir=None):
	"""Build a label while preserving the original path as the selection value."""
	title, checklist_id, estimate = read_scenario_details(path)
	name = title or Path(path).name
	if checklist_id:
		name = f'{checklist_id}: {name}'
	duration = estimate + PRESET_LOADING_ESTIMATE_SECONDS if estimate is not None else None
	label = f'{name} ({format_estimated_duration(duration)})'
	if include_path and scenario_dir is not None:
		try:
			relative_path = Path(path).relative_to(scenario_dir).as_posix()
		except ValueError:
			relative_path = str(path)
		label += f' — {relative_path}'
	return label


def _read_estimates():
	"""Build the compatibility index from scenario files, never importing them."""
	estimates = {}
	for path in sorted((Path(__file__).parent / 'list').rglob('*.py')):
		if path.name == '__init__.py' or '__pycache__' in path.parts:
			continue
		_, checklist_id, estimate = read_scenario_details(path)
		if checklist_id and estimate is not None:
			estimates.setdefault(checklist_id, estimate)
	return estimates


# Compatibility view; scenario class attributes are the source of truth.
SCENARIO_RUN_ESTIMATES = _read_estimates()