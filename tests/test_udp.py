"""Regression tests for the UDP controller address registry."""

import sys
import threading
import types
import unittest
from unittest.mock import patch


main_thread_stub = types.ModuleType("mainThread")
main_thread_stub.taskEnable = lambda: True
sys.modules.setdefault("mainThread", main_thread_stub)

from udp import udp
from udp.message import make_scan_message


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
