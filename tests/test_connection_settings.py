"""Connection settings tests, independent of GUI and controller hardware."""

import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from config import ConfigParserInstance
from connection_settings import DEFAULT_SETTINGS, can_contexts, load_settings, save_settings, validate_settings


class TestConnectionSettings(unittest.TestCase):
	def setUp(self):
		self.directory = tempfile.TemporaryDirectory()
		self.addCleanup(self.directory.cleanup)
		self.path = Path(self.directory.name) / 'settings.ini'
		self.environment = patch.dict(os.environ, {'BRS_SETTINGS_PATH': str(self.path)})
		self.environment.start()
		self.addCleanup(self.environment.stop)
		self.config = self.new_config()

	def new_config(self):
		# Do not replace the application singleton used by unrelated tests.
		config = object.__new__(ConfigParserInstance)
		config.__init__()
		return config

	def test_missing_settings_use_defaults(self):
		self.assertEqual(load_settings(self.config, 'main'), DEFAULT_SETTINGS)

	def test_round_trip_and_profile_isolation(self):
		settings = dict(DEFAULT_SETTINGS, controller_id='123', transport='udp', udp_port='32000')
		saved = save_settings(self.config, 'tester', settings)
		self.assertEqual(saved['controller_id'], 123)
		self.assertEqual(saved['udp_port'], 32000)
		self.assertEqual(load_settings(self.new_config(), 'tester'), saved)
		self.assertEqual(load_settings(self.config, 'main'), DEFAULT_SETTINGS)
		self.assertEqual(self.config.getParameterValue('main', 'preset'), 'district_heating')

	def test_corrupt_values_use_defaults(self):
		for value in ('not json', '[]', 'null', '{"udp_port": 0}', '{"transport": "serial"}'):
			with self.subTest(value=value):
				self.config.setParameterValue('main', 'connection_settings', value)
				self.assertEqual(load_settings(self.config, 'main'), DEFAULT_SETTINGS)

	def test_invalid_values_are_not_saved(self):
		for key, value in (('controller_id', -1), ('controller_id', 256),
				('controller_id', '1.5'), ('controller_id', True), ('udp_port', 0),
				('udp_port', 65536), ('udp_port', 'abc'), ('can_context', ''),
				('transport', 'serial')):
			with self.subTest(key=key, value=value):
				with self.assertRaises(ValueError):
					save_settings(self.config, 'main', dict(DEFAULT_SETTINGS, **{key: value}))
		self.assertEqual(load_settings(self.config, 'main'), DEFAULT_SETTINGS)

	def test_boundaries_and_can_contexts(self):
		for controller_id, port in ((0, 1), (255, 65535)):
			settings = validate_settings(dict(DEFAULT_SETTINGS, controller_id=controller_id, udp_port=port))
			self.assertEqual(settings['controller_id'], controller_id)
			self.assertEqual(settings['udp_port'], port)
		self.assertIn('default', can_contexts())
		self.assertIn('virtual', can_contexts())


if __name__ == '__main__':
	unittest.main()
