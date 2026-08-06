import unittest
import sys
import types
from unittest.mock import patch

# smartnet.message imports mainThread for runtime CAN-loop state.  A minimal
# test stub keeps these pure conversion tests independent of application setup.
main_thread_stub = types.ModuleType('mainThread')
main_thread_stub.taskEnable = lambda: True
sys.modules.setdefault('mainThread', main_thread_stub)

from smartnet.crc16 import CRC16
from smartnet.remoteControl import (
	RemoteControlParameter,
	SCHEDULE_CRC_SELECTOR,
	bytes_to_schedule_crc,
	bytes_to_schedule_value,
	bytes_to_clock_time,
	bytes_to_date,
	clock_time_to_data,
	date_to_data,
	schedule_table_crc,
	schedule_table_to_bytes,
	schedule_value_to_data,
)


class TestScheduleEncoding(unittest.TestCase):
	def test_schedule_value_round_trip(self):
		value = (5, 1439)
		data = schedule_value_to_data(value)

		self.assertEqual(data, [5, 0, 159, 5])
		self.assertEqual(bytes_to_schedule_value(data), value)

	def test_schedule_value_allows_midnight_end(self):
		value = (1110, 1440)
		data = schedule_value_to_data(value)

		self.assertEqual(data, [86, 4, 160, 5])
		self.assertEqual(bytes_to_schedule_value(data), value)

	def test_schedule_value_rejects_invalid_minutes(self):
		with self.assertRaises(ValueError):
			schedule_value_to_data((-1, 0))
		with self.assertRaises(ValueError):
			schedule_value_to_data((1440, 1440))
		with self.assertRaises(ValueError):
			schedule_value_to_data((0, 1441))
		with self.assertRaises(ValueError):
			schedule_value_to_data((0,))

	def test_schedule_crc_uses_all_21_values(self):
		table = [(day * 60, 23 * 60 + 59) for day in range(7) for _ in range(3)]
		raw_data = schedule_table_to_bytes(table)

		self.assertEqual(len(raw_data), 7 * 3 * 4)
		self.assertEqual(schedule_table_crc(table), CRC16.calc(raw_data))

	def test_schedule_crc_is_little_endian(self):
		crc = 0x1234
		self.assertEqual(bytes_to_schedule_crc([0x34, 0x12]), crc)


class TestScheduleParameterConversion(unittest.TestCase):
	def _parameter(self, value, selector):
		return RemoteControlParameter(
			programType=1,
			parameterId=1,
			parameterValue=value,
			parameterIndex=selector,
			programId=1,
		)

	@patch.object(RemoteControlParameter, 'getParameterType', return_value='SCHEDULE')
	def test_schedule_value_conversion(self, _get_type):
		parameter = self._parameter((6 * 60 + 30, 8 * 60 + 45), (6, 2))
		self.assertEqual(parameter.valueToData(parameter.get_value()), [134, 1, 13, 2])
		self.assertEqual(parameter.getParameterSize(), 4)

	@patch.object(RemoteControlParameter, 'getParameterType', return_value='SCHEDULE')
	def test_crc_conversion(self, _get_type):
		parameter = self._parameter(0x1234, SCHEDULE_CRC_SELECTOR)
		self.assertEqual(parameter.valueToData(parameter.get_value()), [0x34, 0x12])
		self.assertEqual(parameter.getParameterSize(), 2)

	@patch.object(RemoteControlParameter, 'getParameterType', return_value='SCHEDULE')
	def test_schedule_selector_validation(self, _get_type):
		valid = self._parameter((1, 2, 3, 4), (6, 2))
		crc = self._parameter(0x1234, SCHEDULE_CRC_SELECTOR)
		invalid = self._parameter((1, 2, 3, 4), (7, 0))

		self.assertTrue(valid._is_schedule_selector_valid())
		self.assertTrue(crc._is_schedule_selector_valid())
		self.assertFalse(invalid._is_schedule_selector_valid())


class TestControllerClockConversion(unittest.TestCase):
	def test_date_round_trip(self):
		value = (3, 0, 8, 2026)
		data = date_to_data(value)

		self.assertEqual(data, [3, 0, 8, 234, 7])
		self.assertEqual(bytes_to_date(data), value)

	def test_time_round_trip(self):
		value = (23, 59, 58, 0)
		data = clock_time_to_data(value)

		self.assertEqual(data, [23, 59, 58, 0])
		self.assertEqual(bytes_to_clock_time(data), value)


if __name__ == '__main__':
	unittest.main()
