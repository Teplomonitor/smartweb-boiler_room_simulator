"""Static validation for BoilerRoomSimulator scenario files.

This validator intentionally uses only the Python AST. It must work without
starting the application, importing GUI modules, opening CAN devices, or
connecting to a controller.
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
from pathlib import Path


REQUIRED_METHODS = {
	'get_scenario_title',
	'get_scenario_description',
	'get_checklist_id',
	'get_required_programs',
	'get_default_preset',
	'run',
}
INHERITABLE_METHODS = {'get_required_programs', 'get_default_preset'}
CHECKLIST_ID_PATTERN = re.compile(r'\b\d+(?:\.\d+)+\b')
DESCRIPTION = 'Static validation for BoilerRoomSimulator scenario files.'


class ScenarioValidator:
	def __init__(self, repository_root: Path):
		self.repository_root = repository_root
		self.scenario_root = repository_root / 'scenario' / 'list'
		self.preset_root = repository_root / 'presets' / 'list'
		self.errors: list[str] = []
		self.warnings: list[str] = []
		self.checklist_ids: dict[str, Path] = {}

	def error(self, path: Path, message: str):
		self.errors.append(f'{self.relative(path)}: error: {message}')

	def warning(self, path: Path, message: str):
		self.warnings.append(f'{self.relative(path)}: warning: {message}')

	def relative(self, path: Path) -> str:
		return str(path.relative_to(self.repository_root)).replace('\\', '/')

	@staticmethod
	def get_class(tree: ast.Module) -> ast.ClassDef | None:
		for node in tree.body:
			if isinstance(node, ast.ClassDef) and node.name == 'Scenario':
				return node
		return None

	@staticmethod
	def get_method(class_node: ast.ClassDef, name: str) -> ast.FunctionDef | None:
		for node in class_node.body:
			if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
				return node
		return None

	@staticmethod
	def get_string_return(function: ast.FunctionDef | None) -> str | None:
		if function is None:
			return None
		for node in ast.walk(function):
			if isinstance(node, ast.Return) and isinstance(node.value, ast.Constant):
				if isinstance(node.value.value, str):
					return node.value.value
		return None

	@staticmethod
	def uses_snc(tree: ast.Module) -> bool:
		return any(
			isinstance(node, ast.Attribute)
			and isinstance(node.value, ast.Name)
			and node.value.id == 'snc'
			for node in ast.walk(tree)
		)

	@staticmethod
	def imports_snc(tree: ast.Module) -> bool:
		for node in tree.body:
			if isinstance(node, ast.Import):
				if any(alias.name == 'smartnet.constants' and alias.asname == 'snc' for alias in node.names):
					return True
		return False

	@staticmethod
	def assigns_status(class_node: ast.ClassDef) -> set[str]:
		result = set()
		for node in ast.walk(class_node):
			if not isinstance(node, ast.Assign):
				continue
			for target in node.targets:
				if (
					isinstance(target, ast.Attribute)
					and isinstance(target.value, ast.Name)
					and target.value.id == 'self'
					and target.attr == '_status'
					and isinstance(node.value, ast.Constant)
					and isinstance(node.value.value, str)
				):
					result.add(node.value.value)
		return result

	def validate_file(self, path: Path):
		try:
			tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
		except (OSError, SyntaxError, UnicodeError) as exc:
			self.error(path, f'cannot parse file: {exc}')
			return

		class_node = self.get_class(tree)
		if class_node is None:
			self.error(path, 'missing class Scenario')
			return

		methods = {node.name for node in class_node.body if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}
		base_names = {
			base.id for base in class_node.bases if isinstance(base, ast.Name)
		}
		uses_specialized_base = any(
			isinstance(node, ast.ImportFrom)
			and node.module is not None
			and node.module.startswith('scenario.base')
			for node in tree.body
		)
		missing_methods = REQUIRED_METHODS - methods
		if uses_specialized_base or base_names - {'Parent'}:
			missing_methods -= INHERITABLE_METHODS
		for method_name in sorted(missing_methods):
			self.error(path, f'missing required method {method_name}()')

		if self.uses_snc(tree) and not self.imports_snc(tree):
			self.error(path, 'uses snc but does not import smartnet.constants as snc')

		checklist_id = self.get_string_return(self.get_method(class_node, 'get_checklist_id'))
		if not checklist_id:
			self.error(path, 'get_checklist_id() must return a non-empty string literal')
		else:
			previous = self.checklist_ids.get(checklist_id)
			if previous is not None:
				self.error(path, f'duplicate checklist ID {checklist_id}; already used by {self.relative(previous)}')
			else:
				self.checklist_ids[checklist_id] = path

		preset = self.get_string_return(self.get_method(class_node, 'get_default_preset'))
		if not preset:
			if 'get_default_preset' in methods or not uses_specialized_base:
				self.error(path, 'get_default_preset() must return a non-empty string literal')
		else:
			preset_path = self.preset_root / f'{preset}.py'
			if not preset_path.is_file():
				self.error(path, f'preset {preset!r} does not exist at {self.relative(preset_path)}')

		statuses = self.assigns_status(class_node)
		if 'OK' not in statuses or 'FAIL' not in statuses:
			self.warning(path, 'scenario should assign both _status = \'OK\' and _status = \'FAIL\'')

		filename_ids = CHECKLIST_ID_PATTERN.findall(path.stem.replace('_', '.'))
		if checklist_id and filename_ids and not any(
			filename_id in checklist_id for filename_id in filename_ids
		):
			self.warning(path, f'filename checklist ID does not match get_checklist_id()={checklist_id}')

	def validate(self) -> int:
		if not self.scenario_root.is_dir():
			self.errors.append(f'{self.relative(self.scenario_root)}: error: scenario directory does not exist')
			return 1

		files = sorted(
			path for path in self.scenario_root.rglob('*.py')
			if path.name != '__init__.py' and '__pycache__' not in path.parts
		)
		if not files:
			self.errors.append(f'{self.relative(self.scenario_root)}: error: no scenario files found')
			return 1

		for path in files:
			self.validate_file(path)

		for message in self.warnings:
			print(message)
		for message in self.errors:
			print(message, file=sys.stderr)
		print(f'Validated {len(files)} scenario files: {len(self.errors)} error(s), {len(self.warnings)} warning(s).')
		return 1 if self.errors else 0


def main() -> int:
	parser = argparse.ArgumentParser(description=DESCRIPTION)
	parser.add_argument(
		'--repository-root',
		type=Path,
		default=Path(__file__).resolve().parents[1],
		help='BoilerRoomSimulator repository root (defaults to the parent of tools/)',
	)
	args = parser.parse_args()
	return ScenarioValidator(args.repository_root.resolve()).validate()


if __name__ == '__main__':
	raise SystemExit(main())
