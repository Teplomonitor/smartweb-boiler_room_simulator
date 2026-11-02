"""Regression tests for the UDP controller address registry."""

import sys
import threading
import types
import unittest
from unittest.mock import Mock, patch

import can


main_thread_stub = types.ModuleType("mainThread")
main_thread_stub.taskEnable = lambda: True
sys.modules.setdefault("mainThread", main_thread_stub)

from udp import udp
from udp.message import can_to_udp, make_scan_message
from smartnet.constants import ControllerFunction, ProgramType, RequestFlag


class TestJournalUdpTrace(unittest.TestCase):
    @staticmethod
    def message(flag):
        header = (ProgramType.CONTROLLER | (209 << 8)
                  | (ControllerFunction['JOURNAL'] << 16) | (flag << 24))
        return can.Message(arbitration_id=header, is_extended_id=True,
                           data=bytes.fromhex('00 00 95 9E E4 9B E7 6A'))

    def make_sender(self):
        sender = udp.can_thread.__new__(udp.can_thread)
        sender._port = 31987
        sender._canbus = Mock()
        sender._canbus.recv.return_value = None
        sender._udp_messages_to_send = bytearray(can_to_udp(self.message(RequestFlag['REQUEST'])))
        sender._send_can_time = 99
        sender._send_scan_time = 100
        sender.send_udp_packet = Mock()
        return sender

    def test_sent_datagram_is_logged_after_send(self):
        sender = self.make_sender()
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), \
                patch.object(udp, 'ip_list', {'192.168.10.54': 100}), \
                patch.object(udp.time, 'time', return_value=100), \
                patch.object(udp, 'print_log') as log:
            sender.do_run()
        sender.send_udp_packet.assert_called_once()
        self.assertIn('UDP_TX peer=192.168.10.54:31987 id=0015D10B dlc=8 '
                      'data=00 00 95 9E E4 9B E7 6A', log.call_args.args[0])

    def test_missing_destination_is_not_reported_as_sent(self):
        sender = self.make_sender()
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), \
                patch.object(udp, 'ip_list', {}), \
                patch.object(udp.time, 'time', return_value=100), \
                patch.object(udp, 'print_log') as log:
            sender.do_run()
        sender.send_udp_packet.assert_not_called()
        self.assertIn('UDP_NO_DESTINATION', log.call_args.args[0])

    def test_udp_send_error_is_logged_and_propagated(self):
        sender = self.make_sender()
        sender.send_udp_packet.side_effect = OSError('send failed')
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), \
                patch.object(udp, 'ip_list', {'192.168.10.54': 100}), \
                patch.object(udp.time, 'time', return_value=100), \
                patch.object(udp, 'print_log') as log:
            with self.assertRaises(OSError):
                sender.do_run()
        self.assertIn('UDP_TX_ERROR', log.call_args.args[0])

    def test_received_datagram_is_logged_and_forwarded(self):
        receiver = udp.udp_listen_thread.__new__(udp.udp_listen_thread)
        receiver._sock = Mock()
        receiver._sock.recvfrom.return_value = (can_to_udp(self.message(RequestFlag['RESPONSE'])),
                                                ('192.168.10.54', 31987))
        receiver._canbus = Mock()
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), \
                patch.object(udp, 'self_ip_list', []), \
                patch.object(udp, 'ip_list', {'192.168.10.54': 100}), \
                patch.object(udp, 'print_log') as log:
            receiver.do_run()
        receiver._canbus.send.assert_called_once()
        self.assertIn('UDP_RX peer=192.168.10.54:31987 id=1015D10B', log.call_args.args[0])

    def test_trace_disabled(self):
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '0'}), patch.object(udp, 'print_log') as log:
            udp.trace_journal_udp('TX', [self.message(RequestFlag['REQUEST'])], 'test')
        log.assert_not_called()

    def test_non_journal_message_is_not_traced(self):
        other = self.message(RequestFlag['REQUEST'])
        other.arbitration_id ^= 1 << 16
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), patch.object(udp, 'print_log') as log:
            udp.trace_journal_udp('TX', [other], 'test')
        log.assert_not_called()


class TestUdpControllerRegistry(unittest.TestCase):
    def setUp(self):
        with udp.ip_list_lock:
            udp.ip_list.clear()

    def tearDown(self):
        with udp.ip_list_lock:
            udp.ip_list.clear()

    @staticmethod
    def scan_message():
        return make_scan_message(bytearray(b"remote-controller"))

    def test_expired_controller_is_removed_and_can_be_found_again(self):
        message = self.scan_message()

        with patch.object(udp.time, "time", side_effect=(1000, 1601, 1601)):
            self.assertEqual(
                udp.update_ip_list(message, "192.168.43.193"),
                "NEW_CONTROLLER_FOUND",
            )
            self.assertEqual(
                udp.update_ip_list(message, "192.168.43.194"),
                "NEW_CONTROLLER_FOUND",
            )
            self.assertEqual(
                udp.update_ip_list(message, "192.168.43.193"),
                "NEW_CONTROLLER_FOUND",
            )

        with udp.ip_list_lock:
            self.assertEqual(set(udp.ip_list), {"192.168.43.193", "192.168.43.194"})

    def test_concurrent_updates_leave_registry_consistent(self):
        message = self.scan_message()
        errors = []

        def update(index):
            try:
                udp.update_ip_list(message, f"192.168.43.{index}")
            except Exception as error:  # pragma: no cover - assertion reports details
                errors.append(error)

        with patch.object(udp.time, "time", return_value=1000):
            threads = [threading.Thread(target=update, args=(index,)) for index in range(1, 51)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()

        self.assertEqual(errors, [])
        with udp.ip_list_lock:
            self.assertEqual(len(udp.ip_list), 50)


if __name__ == "__main__":
    unittest.main()
