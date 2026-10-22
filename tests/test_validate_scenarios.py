import tempfile
import unittest
from pathlib import Path

from tools.validate_scenarios import ScenarioValidator


VALID_SCENARIO = '''
from scenario.scenario import Scenario as Parent


class Scenario(Parent):
	def get_scenario_title(self):
		return 'Valid scenario'

	def get_scenario_description(self):
		return 'A valid scenario fixture.'

	def get_checklist_id(self):
		return '1.2.3'

	def get_required_programs(self):
		return []

	def get_default_preset(self):
		return 'default'

	def run(self):
		self._status = 'OK'
		self._status = 'FAIL'
'''


class TestScenarioValidator(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.TemporaryDirectory()
		self.root = Path(self.directory.name)
		(self.root / 'scenario' / 'list').mkdir(parents=True)
		(self.root / 'presets' / 'list').mkdir(parents=True)

	def tearDown(self):
		self.directory.cleanup()

	def _write_scenario(self, name, content=VALID_SCENARIO):
		path = self.root / 'scenario' / 'list' / name
		path.write_text(content, encoding='utf-8')
		return path

	def _write_preset(self, name='default'):
		(self.root / 'presets' / 'list' / f'{name}.py').write_text('', encoding='utf-8')

	def _write_base(self, content, name='dispatch'):
		base_dir = self.root / 'scenario' / 'base'
		base_dir.mkdir(exist_ok=True)
		(base_dir / f'{name}.py').write_text(content, encoding='utf-8')

	def _write_delegating_scenario(self, call='self.execute()'):
		self._write_preset()
		self._write_scenario('scenario_1_2_3.py', VALID_SCENARIO.replace(
			'from scenario.scenario import Scenario as Parent',
			'from scenario.base.dispatch import Dispatch as Parent',
		).replace(
			"\t\tself._status = 'OK'\n\t\tself._status = 'FAIL'",
			f"\t\tself._status = 'FAIL'\n\t\t{call}",
		))

	def test_called_inherited_status_is_recognized_without_importing(self):
		self._write_delegating_scenario()
		self._write_base('''
raise RuntimeError('The validator must not import this module')

class Dispatch:
	def execute(self):
		self._status = 'OK'
''')
		validator = ScenarioValidator(self.root)
		self.assertEqual(validator.validate(), 0)
		self.assertEqual(validator.warnings, [])

	def test_unused_inherited_status_does_not_suppress_warning(self):
		self._write_delegating_scenario(call='pass')
		self._write_base("class Dispatch:\n\tdef execute(self):\n\t\tself._status = 'OK'\n")
		validator = ScenarioValidator(self.root)
		self.assertEqual(validator.validate(), 0)
		self.assertTrue(any('both _status' in warning for warning in validator.warnings))

	def test_overridden_inherited_status_does_not_suppress_warning(self):
		self._write_delegating_scenario()
		path = self.root / 'scenario/list/scenario_1_2_3.py'
		path.write_text(path.read_text(encoding='utf-8') + '\n\tdef execute(self):\n\t\tpass\n', encoding='utf-8')
		self._write_base("class Dispatch:\n\tdef execute(self):\n\t\tself._status = 'OK'\n")
		validator = ScenarioValidator(self.root)
		self.assertEqual(validator.validate(), 0)
		self.assertTrue(any('both _status' in warning for warning in validator.warnings))

	def test_multilevel_aliased_inheritance_and_helper_calls(self):
		self._write_delegating_scenario()
		self._write_base('''
from scenario.base.common import Common as Ancestor

class Dispatch(Ancestor):
	def execute(self):
		self.finish()
''')
		self._write_base("class Common:\n\tdef finish(self):\n\t\tself._status = 'OK'\n", name='common')
		validator = ScenarioValidator(self.root)
		self.assertEqual(validator.validate(), 0)
		self.assertEqual(validator.warnings, [])

	def test_cyclic_inheritance_and_calls_terminate_with_warning(self):
		self._write_delegating_scenario()
		self._write_base('''
from scenario.base.dispatch import Dispatch as Again

class Dispatch(Again):
	def execute(self):
		self.execute()
''')
		validator = ScenarioValidator(self.root)
		self.assertEqual(validator.validate(), 0)
		self.assertTrue(any('both _status' in warning for warning in validator.warnings))

	def test_unresolved_base_does_not_suppress_warning(self):
		self._write_delegating_scenario()
		for content in (None, 'invalid python !', 'class Other: pass'):
			with self.subTest(content=content):
				if content is not None:
					self._write_base(content)
				validator = ScenarioValidator(self.root)
				self.assertEqual(validator.validate(), 0)
				self.assertTrue(any('both _status' in warning for warning in validator.warnings))

	def test_valid_scenario_passes(self):
		self._write_preset()
		self._write_scenario('scenario_1_2_3.py')

		validator = ScenarioValidator(self.root)

		self.assertEqual(validator.validate(), 0)
		self.assertEqual(validator.errors, [])

	def test_missing_preset_is_reported(self):
		path = self._write_scenario('scenario_1_2_3.py')

		validator = ScenarioValidator(self.root)

		self.assertEqual(validator.validate(), 1)
		self.assertTrue(any('preset' in error for error in validator.errors))
		relative_path = str(path.relative_to(self.root)).replace('\\', '/')
		self.assertTrue(any(relative_path in error for error in validator.errors))

	def test_duplicate_checklist_id_is_reported(self):
		self._write_preset()
		self._write_scenario('scenario_1_2_3.py')
		self._write_scenario('scenario_copy_1_2_3.py')

		validator = ScenarioValidator(self.root)

		self.assertEqual(validator.validate(), 1)
		self.assertTrue(any('duplicate checklist ID 1.2.3' in error for error in validator.errors))

	def test_missing_scenario_directory_is_reported(self):
		root = self.root / 'empty'
		root.mkdir()

		validator = ScenarioValidator(root)

		self.assertEqual(validator.validate(), 1)
		self.assertTrue(any('scenario/list' in error for error in validator.errors))


if __name__ == '__main__':
	unittest.main()
