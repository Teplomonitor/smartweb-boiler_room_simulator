import threading
import unittest
from unittest.mock import Mock

from scenario.scenario import ScenarioThread


class TestScenarioSelection(unittest.TestCase):
	def setUp(self):
		self.thread = object.__new__(ScenarioThread)
		self.thread._scenarioList = ['first.py', 'second.py', 'third.py']
		self.thread._scenarioQueue = []
		self.thread._stopScenarioEvent = threading.Event()

	def test_all_selection_queues_every_scenario(self):
		queue = self.thread.get_scenario_queue('all')

		self.assertEqual(queue, self.thread._scenarioList)
		self.assertIsNot(queue, self.thread._scenarioList)

	def test_single_selection_is_queued(self):
		self.assertEqual(
			self.thread.get_scenario_queue('second.py'),
			['second.py'],
		)

	def test_multiple_selection_preserves_order(self):
		self.assertEqual(
			self.thread.get_scenario_queue(['third.py', 'first.py']),
			['third.py', 'first.py'],
		)

	def test_empty_selection_is_finished_without_scenarios(self):
		self.assertEqual(self.thread.get_scenario_queue([]), [])

	def test_invalid_selection_is_rejected(self):
		self.assertIsNone(
			self.thread.get_scenario_queue(['first.py', 'missing.py']),
		)

	def test_next_scenario_consumes_queue_in_order(self):
		self.thread._scenarioQueue = ['third.py', 'first.py']
		self.thread.get_scenario_object = Mock(side_effect=lambda scenario_id: scenario_id)

		self.assertEqual(self.thread.getNextScenario(), 'third.py')
		self.assertEqual(self.thread.getNextScenario(), 'first.py')
		self.assertIsNone(self.thread.getNextScenario())
		self.assertEqual(
			self.thread.get_scenario_object.call_args_list,
			[
				unittest.mock.call('third.py'),
				unittest.mock.call('first.py'),
			],
		)


if __name__ == '__main__':
	unittest.main()
