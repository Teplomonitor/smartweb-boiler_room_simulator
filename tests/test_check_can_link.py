"""CAN round-trip diagnostic tests; no physical bus or controller is used."""

import unittest
from unittest.mock import patch

import can
from smartnet import constants as snc
from tools import check_can_link


class FakeBus:
	def __init__(self, frames):
		self.frames = list(frames)
		self.sent = []
		self.closed = False

	def __enter__(self):
		return self

	def __exit__(self, *args):
		self.closed = True

	def recv(self, timeout):
		return self.frames.pop(0) if self.frames else None

	def send(self, message):
		self.sent.append(message)


def response(controller_id, function, data):
	header = (int(snc.ProgramType.CONTROLLER) | (controller_id << 8)
		| (int(function) << 16) | (int(snc.RequestFlag.RESPONSE) << 24))
	return can.Message(arbitration_id=header, is_extended_id=True, data=data)


class TestCanLink(unittest.TestCase):
	def test_read_only_request_matches_selected_controller_and_closes_bus(self):
		bus = FakeBus([
			response(209, snc.ControllerFunction.I_AM_HERE, [snc.ControllerType.SWK]),
			response(96, snc.ControllerFunction.GET_ACTIVE_PROGRAMS_LIST, [99, 16]),
			response(209, snc.ControllerFunction.GET_ACTIVE_PROGRAMS_LIST, [101, 16, 102, 23]),
		])
		with patch.object(check_can_link, 'load_config', return_value={
			'interface': 'gs_usb', 'channel': 0, 'index': 0, 'bitrate': 20000
		}):
			self.assertEqual(check_can_link.check_bus('ucan',
				bus_factory=lambda **_kwargs: bus), (209, [(101, 16), (102, 23)]))
		self.assertTrue(bus.closed)
		self.assertEqual(len(bus.sent), 1)
		sent = bus.sent[0]
		self.assertTrue(sent.is_extended_id)
		self.assertEqual(sent.arbitration_id & 0xFF, snc.ProgramType.CONTROLLER)
		self.assertEqual((sent.arbitration_id >> 8) & 0xFF, 209)
		self.assertEqual((sent.arbitration_id >> 16) & 0xFF,
			snc.ControllerFunction.GET_ACTIVE_PROGRAMS_LIST)
		self.assertEqual((sent.arbitration_id >> 24) & 0xFF, snc.RequestFlag.REQUEST)

	def test_timeout_still_closes_bus_and_does_not_send_mutations(self):
		bus = FakeBus([response(209, snc.ControllerFunction.I_AM_HERE, [10])])
		with patch.object(check_can_link, 'load_config', return_value={'interface': 'gs_usb'}):
			with self.assertRaises(TimeoutError):
				check_can_link.check_bus('ucan', bus_factory=lambda **_kwargs: bus,
					response_timeout=0.01)
		self.assertTrue(bus.closed)
		self.assertEqual(len(bus.sent), 1)

	def test_virtual_interface_is_rejected_without_opening_bus(self):
		with patch.object(check_can_link, 'load_config', return_value={'interface': 'virtual'}):
			with self.assertRaises(ValueError):
				check_can_link.check_bus('virtual', bus_factory=lambda **_kwargs:
					self.fail('opened a virtual bus'))


if __name__ == '__main__':
	unittest.main()
