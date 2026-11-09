"""CAN frame rejection and transport failures without USB/controller hardware."""

import io
import json
from pathlib import Path
import tempfile
import threading
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import can

import debug
import mainThread
import parallel_can
from smartnet import message


def invalid_frames():
	return [can.Message(arbitration_id=0x123, is_extended_id=False),
		can.Message(arbitration_id=0x123, is_remote_frame=True),
		can.Message(arbitration_id=0x40, is_error_frame=True),
		can.Message(arbitration_id=0x123, is_fd=True)]


class TestCanFrameDiagnostics(unittest.TestCase):
	def test_rejected_frame_clears_previous_parse_without_printing(self):
		parsed = message.Message()
		for frame in [*invalid_frames(), None]:
			with self.subTest(frame=frame), patch('builtins.print') as output:
				self.assertTrue(parsed.parse(can.Message(arbitration_id=0x01020304, data=[1, 2])))
				self.assertFalse(parsed.parse(frame))
				self.assertIsNone(parsed.get_program_type())
				self.assertIsNone(parsed.get_data())
				output.assert_not_called()

	def test_only_valid_frames_reach_subscribers(self):
		listener = object.__new__(message.CanListener)
		listener._frame_diagnostics = message.CanFrameDiagnostics('ucan')
		subscriber = Mock()
		with patch.object(message.CanListener, '_listeners', [subscriber]), \
				patch.object(message, 'print_error'):
			listener.on_message_received(None)
			for frame in invalid_frames():
				listener.on_message_received(frame)
			subscriber.on_can_message_received.assert_not_called()
			listener.on_message_received(can.Message(arbitration_id=0x01020304, data=[5, 6]))
		subscriber.on_can_message_received.assert_called_once()
		parsed = subscriber.on_can_message_received.call_args.args[0]
		self.assertEqual(parsed.getHeader(), 0x01020304)
		self.assertEqual(parsed.get_data(), bytearray([5, 6]))
		self.assertEqual(listener._frame_diagnostics.accepted, 1)
		self.assertEqual(listener._frame_diagnostics.rejected, 4)

	def test_flood_is_rate_limited_but_counters_and_details_are_preserved(self):
		diagnostics = message.CanFrameDiagnostics('candleLightGsUsb')
		frame = can.Message(arbitration_id=0x40, is_extended_id=False,
			is_error_frame=True, data=[0, 1], timestamp=123)
		with patch.object(message.time, 'monotonic', return_value=0), \
				patch.object(message, 'print_error') as log:
			for _ in range(1000):
				diagnostics.reject(frame)
			self.assertEqual(log.call_count, message.FRAME_LOG_SAMPLES)
			with patch.object(message.time, 'monotonic', return_value=message.FRAME_LOG_INTERVAL):
				diagnostics.reject(frame)
			self.assertEqual(log.call_count, message.FRAME_LOG_SAMPLES + 1)
			text = log.call_args.args[0]
		for detail in ('candleLightGsUsb', 'ID=0x00000040', 'EXT=0', 'ERR=1',
				'DLC=2', 'data=00 01', 'rejected=1001', "'error': 1001"):
			self.assertIn(detail, text)
		self.assertEqual(message.CanFrameDiagnostics('other').rejected, 0)

	def test_debug_responder_does_not_inspect_rejected_frames(self):
		listener = object.__new__(debug.debug_thread)
		with patch.object(debug, 'programsResetFilter') as reset:
			for frame in invalid_frames():
				listener.on_message_received(frame)
			reset.assert_not_called()

	def make_bus(self):
		return SimpleNamespace(send=Mock(), channel_info='usb',
			_brs_can_context='ucan', _brs_gs_usb=True)

	def test_stopped_application_never_sends(self):
		stop = threading.Event()
		stop.set()
		bus = self.make_bus()
		with patch.object(mainThread, '_application', SimpleNamespace(stop_event=stop)):
			message.Message(1, 2, 3, 0, [4]).send(bus=bus)
		bus.send.assert_not_called()

	def test_stop_interrupts_retry_wait_and_prevents_further_sends(self):
		bus = self.make_bus()
		bus.send.side_effect = can.CanOperationError('USB failure')
		stop = Mock()
		stop.is_set.return_value = False
		stop.wait.return_value = True
		with patch.object(mainThread, '_application', SimpleNamespace(stop_event=stop)), \
				patch.object(mainThread, 'report_can_failure') as failure, \
				patch.object(message, 'print_error'):
			message.Message(1, 2, 3, 0, [4]).send(bus=bus)
		bus.send.assert_called_once()
		stop.wait.assert_called_once_with(message.SEND_RETRY_DELAY)
		failure.assert_not_called()

	def test_persistent_gs_usb_send_failure_preserves_cause_and_stops_session(self):
		bus = self.make_bus()
		error = can.CanOperationError('The message could not be sent')
		error.__cause__ = OSError('USB device disconnected')
		bus.send.side_effect = error
		with patch.object(mainThread, '_application', None), \
				patch.object(mainThread, 'report_can_failure') as failure, \
				patch.object(message, 'print_error') as log, \
				patch.object(message.time, 'sleep'):
			message.Message(1, 2, 3, 0, [4]).send(bus=bus)
		self.assertEqual(bus.send.call_count, message.SEND_ATTEMPTS)
		self.assertEqual(log.call_count, 1)
		failure.assert_called_once()
		self.assertIn('USB device disconnected', str(failure.call_args.args[0]))
		self.assertIn('ucan', str(failure.call_args.args[0]))

	def test_transient_send_failure_recovers_without_stopping_session(self):
		bus = self.make_bus()
		bus.send.side_effect = [can.CanOperationError('temporary'), None]
		with patch.object(mainThread, '_application', None), \
				patch.object(mainThread, 'report_can_failure') as failure, \
				patch.object(message, 'print_error'), patch.object(message.time, 'sleep'):
			message.Message(1, 2, 3, 0, [4]).send(bus=bus)
		self.assertEqual(bus.send.call_count, 2)
		failure.assert_not_called()

	def test_worker_reports_fatal_error_after_becoming_ready(self):
		stop = threading.Event()
		worker = Mock(error=None)
		worker.ready_event = threading.Event()
		worker.ready_event.set()
		app = Mock(worker=worker, stop_event=stop)
		def fail(_path):
			worker.error = RuntimeError('CAN ucan: USB disconnected')
			stop.set()
		worker._scenario_thread.start_scenario.side_effect = fail
		commands = io.StringIO(json.dumps({'type': 'run', 'scenario': 'one.py'}) + '\n')
		with patch.object(parallel_can, 'Application', return_value=app), \
				patch('sys.stdin', commands), patch.object(parallel_can, 'send_event') as event:
			self.assertEqual(parallel_can.run_worker(None), 2)
		fatal = event.call_args.args[0]
		self.assertTrue(fatal['fatal'])
		self.assertIn('USB disconnected', fatal['error'])
		app.shutdown.assert_called_once()

	def test_coordinator_retires_failed_connection_and_continues_others(self):
		assignments = []
		class FakeWorker:
			def __init__(self, context, index, args, run_dir, events):
				self.context = context
				self.current = None
				self.ready = False
				self.retiring = False
				self.events = events
				self.process = Mock()
				self.process.poll.return_value = None
				events.put((self, {'type': 'ready'}))
			def send(self, command):
				assignments.append((self.context, command['scenario']))
				if self.context == 'udp_31987':
					self.events.put((self, {'type': 'error', 'fatal': True,
						'error': 'CAN failure: original USB cause'}))
				else:
					self.events.put((self, {'type': 'result', 'checklistId': 'test',
						'result': 'OK', 'duration': 1}))
			def stop(self):
				pass
			def join(self):
				pass
		args = SimpleNamespace(can_ports=[], udp_ports=['31987', '31988'], udp=0,
			debug=False, gui=False, scenario='all')
		with tempfile.TemporaryDirectory() as temp_dir:
			with patch.object(parallel_can, 'CanWorker', FakeWorker), \
					patch.object(parallel_can, 'select_scenarios', return_value=['a', 'b', 'c', 'd']), \
					patch.object(parallel_can.tempfile, 'mkdtemp', return_value=temp_dir):
				self.assertEqual(parallel_can.run_coordinator(args), 2)
			results = json.loads((Path(temp_dir) / 'results.json').read_text(encoding='utf-8'))
		self.assertEqual(sum(r['result'] == 'OK' for r in results), 3)
		self.assertEqual([r['error'] for r in results if r['result'] == 'ERROR'],
			['CAN failure: original USB cause'])
		self.assertEqual(sum(context == 'udp_31987' for context, _ in assignments), 1)


if __name__ == '__main__':
	unittest.main()
