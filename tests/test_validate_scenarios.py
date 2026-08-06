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
