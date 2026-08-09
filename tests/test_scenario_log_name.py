import unittest

from scenario.scenario import sanitize_scenario_log_name


class TestSanitizeScenarioLogName(unittest.TestCase):
	def test_preserves_simple_checklist_id(self):
		self.assertEqual(sanitize_scenario_log_name('3.12.4'), '3.12.4')

	def test_replaces_whitespace_and_invalid_windows_characters(self):
		value = '3.11.7 & 3.11.9: alarm/pump?'
		self.assertEqual(
			sanitize_scenario_log_name(value),
			'3.11.7_&_3.11.9_alarm_pump',
		)

	def test_removes_trailing_dots_and_spaces(self):
		self.assertEqual(sanitize_scenario_log_name('scenario.  '), 'scenario')

	def test_uses_fallback_for_empty_values(self):
		self.assertEqual(sanitize_scenario_log_name(None), 'scenario')
		self.assertEqual(sanitize_scenario_log_name(' \\ / '), 'scenario')


if __name__ == '__main__':
	unittest.main()
