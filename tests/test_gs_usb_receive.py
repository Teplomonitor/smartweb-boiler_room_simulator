"""GS-USB receive recovery tests without CAN or USB hardware."""

import struct
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import can
from can.interfaces.gs_usb import GsUsbBus
from gs_usb.constants import GS_CAN_MODE_HW_TIMESTAMP
from gs_usb.gs_usb import GsUsb
from gs_usb.gs_usb_frame import GsUsbFrame
import usb.core

import mainThread
from smartnet import can_adapter, message


def make_device(responses, timestamp=True):
	usb_device = Mock()
	usb_device.read.side_effect = responses
	device = GsUsb(usb_device)
	device.device_flags = GS_CAN_MODE_HW_TIMESTAMP if timestamp else 0
	return device


def valid_frame(timestamp=True):
	values = (0xffffffff, 0x80000001, 1, 0, 0, 0, *range(8))
	return struct.pack('<2I12BI', *values, 123) if timestamp else struct.pack('<2I12B', *values)


class TestGsUsbReceive(unittest.TestCase):
	def test_short_frame_is_discarded_and_next_frame_is_received(self):
		for timestamp in (True, False):
			with self.subTest(timestamp=timestamp):
				device = make_device([b'\x00' * 3, valid_frame(timestamp)], timestamp)
				failure = Mock()
				with patch.object(can_adapter, 'print_error') as log:
					can_adapter.protect_gs_usb_receive(SimpleNamespace(gs_usb=device), 'ucan', failure)
					frame = GsUsbFrame()
					self.assertFalse(device.read(frame, 10))
					self.assertTrue(device.read(frame, 10))
				self.assertEqual(frame.can_id, 0x80000001)
				self.assertEqual(frame.data[:1], [0])
				self.assertIn(f'expected {24 if timestamp else 20}', log.call_args.args[0])
				failure.assert_not_called()

	def test_five_errors_within_window_stop_only_once(self):
		device = make_device([b'\x00' * 20] * 5)
		failure = Mock()
		with (patch.object(can_adapter, 'print_error') as log,
				patch.object(can_adapter.time, 'monotonic', side_effect=[0, 1, 2, 3, 10]),
				patch.object(can_adapter.time, 'sleep') as sleep):
			can_adapter.protect_gs_usb_receive(SimpleNamespace(gs_usb=device), 'candleLightGsUsb', failure)
			for _ in range(6):
				self.assertFalse(device.read(GsUsbFrame(), 1000))
		failure.assert_called_once()
		self.assertIn('candleLightGsUsb', str(failure.call_args.args[0]))
		self.assertIn('20 bytes, expected 24', str(failure.call_args.args[0]))
		self.assertEqual(log.call_count, 1)
		self.assertEqual(device.gs_usb.read.call_count, 5)
		sleep.assert_called_once_with(can_adapter.FAILED_RECEIVE_POLL_DELAY)

	def test_errors_outside_window_do_not_accumulate(self):
		device = make_device([b''] * 5)
		failure = Mock()
		with (patch.object(can_adapter, 'print_error') as log,
				patch.object(can_adapter.time, 'monotonic', side_effect=[0, 1, 2, 3, 11])):
			can_adapter.protect_gs_usb_receive(SimpleNamespace(gs_usb=device), 'ucan', failure)
			for _ in range(5):
				self.assertFalse(device.read(GsUsbFrame(), 1))
		failure.assert_not_called()
		self.assertEqual(log.call_count, 1)

	def test_unrelated_struct_error_is_not_suppressed(self):
		device = SimpleNamespace(read=Mock(side_effect=struct.error('unrelated')))
		failure = Mock()
		can_adapter.protect_gs_usb_receive(SimpleNamespace(gs_usb=device), 'ucan', failure)
		with self.assertRaisesRegex(struct.error, 'unrelated'):
			device.read(GsUsbFrame(), 1)
		failure.assert_not_called()

	def test_real_notifier_survives_short_frame_then_reports_burst(self):
		device = make_device([b'\x00' * 20, valid_frame()] + [b'\x00' * 20] * 4)
		bus = object.__new__(GsUsbBus)
		bus.gs_usb = device
		bus.channel_info = 'test'
		can.BusABC.__init__(bus, channel='test')
		received = []
		failed = threading.Event()
		failures = []
		def on_failure(error):
			failures.append(error)
			failed.set()
		with patch.object(can_adapter, 'print_error'):
			can_adapter.protect_gs_usb_receive(bus, 'ucan', on_failure)
			notifier = can.Notifier(bus, [received.append], timeout=0.01)
			try:
				self.assertTrue(failed.wait(2), 'CAN failure was not reported')
			finally:
				notifier.stop(timeout=2)
		self.assertEqual(len(received), 1)
		self.assertEqual(received[0].arbitration_id, 1)
		self.assertEqual(len(failures), 1)
		self.assertIsNone(notifier.exception)
		# The test bypasses GsUsbBus.__init__, so do not invoke its hardware shutdown.
		bus._is_shutdown = True

	def test_both_named_profiles_install_guard_and_virtual_does_not(self):
		for profile, interface in [('ucan', 'gs_usb'), ('candleLightGsUsb', 'gs_usb'),
				('virtual', 'virtual')]:
			with self.subTest(profile=profile), \
					patch.object(message, 'resolve_bus_config', return_value={'interface': interface}), \
					patch.object(message.can, 'Bus') as factory, \
					patch.object(message, 'protect_gs_usb_receive') as protect:
				self.assertIs(message.createBus(profile), factory.return_value)
				if interface == 'gs_usb':
					protect.assert_called_once_with(factory.return_value, profile, mainThread.report_can_failure)
				else:
					protect.assert_not_called()

	def test_fatal_error_stops_application_and_preserves_error(self):
		worker = SimpleNamespace(error=None)
		application = SimpleNamespace(worker=worker, request_stop=Mock())
		error = RuntimeError('CAN receive failure')
		with patch.object(mainThread, '_application', application), patch.object(mainThread, 'print_error'):
			mainThread.report_can_failure(error)
		self.assertIs(worker.error, error)
		application.request_stop.assert_called_once()


if __name__ == '__main__':
	unittest.main()