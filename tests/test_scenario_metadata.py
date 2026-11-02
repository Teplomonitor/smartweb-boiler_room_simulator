import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from scenario.metadata import (
	PRESET_LOADING_ESTIMATE_SECONDS, SCENARIO_RUN_ESTIMATES,
	format_estimated_duration, get_estimated_duration, read_scenario_metadata, scenario_label,
)


ROOT = Path(__file__).resolve().parents[1]
SCENARIO_ROOT = ROOT / 'scenario' / 'list'


class TestScenarioMetadata(unittest.TestCase):
	def test_all_discovered_scenarios_have_titles_and_estimates(self):
		ids = []
		for path in SCENARIO_ROOT.rglob('*.py'):
			if path.name == '__init__.py':
				continue
			with self.subTest(path=path):
				title, checklist_id = read_scenario_metadata(path)
				self.assertTrue(title)
				self.assertTrue(checklist_id)
				self.assertIn(checklist_id, SCENARIO_RUN_ESTIMATES)
				self.assertEqual(get_estimated_duration(checklist_id),
					SCENARIO_RUN_ESTIMATES[checklist_id] + PRESET_LOADING_ESTIMATE_SECONDS)
				ids.append(checklist_id)
		self.assertEqual(set(ids), set(SCENARIO_RUN_ESTIMATES))
		self.assertEqual(len(ids), len(set(ids)))

	def test_duration_format_and_unknown(self):
		self.assertEqual(PRESET_LOADING_ESTIMATE_SECONDS, 10)
		self.assertEqual(get_estimated_duration('5.2.3.3'), 230)
		self.assertEqual(format_estimated_duration(230), '≈ 3 мин 50 с')
		self.assertEqual(format_estimated_duration(3900), '≈ 1 ч 5 мин')
		self.assertEqual(format_estimated_duration(None), 'время неизвестно')
		self.assertIsNone(get_estimated_duration('not-a-scenario'))

	def test_label_does_not_execute_scenario(self):
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / 'scenario.py'
			path.write_text("raise RuntimeError('must not execute')\n"
				"class Scenario:\n"
				" def get_scenario_title(self): return 'Example'\n"
				" def get_checklist_id(self): return '5.2.3.3'\n", encoding='utf-8')
			self.assertEqual(scenario_label(path, True, directory),
				'5.2.3.3: Example (≈ 3 мин 50 с) — scenario.py')

	def test_missing_invalid_and_dynamic_metadata_are_selectable(self):
		with tempfile.TemporaryDirectory() as directory:
			path = Path(directory) / 'broken.py'
			for contents in (None, 'not python !',
					'class Scenario:\n def get_checklist_id(self): return self.value\n'):
				if contents is not None:
					path.write_text(contents, encoding='utf-8')
				with self.subTest(contents=contents):
					self.assertEqual(read_scenario_metadata(path), (None, None))
					self.assertIn('broken.py (время неизвестно)', scenario_label(path))

	def test_base_scenario_exposes_estimate_without_initialization(self):
		from scenario.scenario import Scenario
		class Example(Scenario):
			def get_checklist_id(self):
				return '5.2.3.3'
		self.assertEqual(Example.__new__(Example).get_estimated_duration(), 230)

	@unittest.skipUnless(os.name == 'nt', 'wx GUI integration requires a Windows desktop')
	def test_selection_dialog_keeps_paths_separate_from_labels(self):
		import wx
		from gui.frame import ScenarioSelectionDialog
		app = wx.GetApp() or wx.App(False)
		path = str(SCENARIO_ROOT / 'heating_circuit' /
			'scenario_heating_circuit_external_priority_5_2_3_3.py')
		dialog = ScenarioSelectionDialog(None, [path], [path])
		try:
			self.assertIn('≈ 3 мин 50 с', dialog._scenario_check_list.GetString(0))
			self.assertTrue(dialog._scenario_check_list.IsChecked(0))
			wx.CallAfter(dialog.on_run, None)
			self.assertEqual(dialog.ShowModal(), wx.ID_OK)
			self.assertEqual(dialog.selected_scenarios, [path])
		finally:
			dialog.Destroy()
			self.assertIsNotNone(app)

	@unittest.skipUnless(os.name == 'nt', 'wx GUI integration requires a Windows desktop')
	def test_scenario_menu_keeps_path_and_literal_ampersand(self):
		import wx
		from gui.frame import MainFrame
		app = wx.GetApp() or wx.App(False)
		frame = wx.Frame(None)
		frame.m_menu1 = wx.Menu()
		frame.onScenarioSelection = lambda event: None
		try:
			MainFrame.addScenarioMenu(frame)
			def all_items(menu):
				for item in menu.GetMenuItems():
					yield item
					if item.GetSubMenu():
						yield from all_items(item.GetSubMenu())
			items = list(all_items(frame.m_menu1))
			item = next(item for item in items if item.GetItemLabelText().startswith('5.2.3.3:'))
			self.assertIn('≈ 3 мин 50 с', item.GetItemLabelText())
			self.assertTrue(any('3.11.7 & 3.11.9:' in item.GetItemLabelText() for item in items))
			with patch('scenario.scenario.start_scenario') as start:
				event = wx.CommandEvent(wx.EVT_MENU.typeId, item.GetId())
				frame.GetEventHandler().ProcessEvent(event)
				start.assert_called_once_with(str(SCENARIO_ROOT / 'heating_circuit' /
					'scenario_heating_circuit_external_priority_5_2_3_3.py'))
		finally:
			frame.m_menu1.Destroy()
			frame.Destroy()
			self.assertIsNotNone(app)


if __name__ == '__main__':
	unittest.main()