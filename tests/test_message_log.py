'''
Unit tests for the Message Log module

Tests CRC16 calculation, message packing/unpacking, and entry creation
'''

import unittest
import struct
import sys
import types
from itertools import permutations
from unittest.mock import patch


main_thread_stub = types.ModuleType('mainThread')
main_thread_stub.taskEnable = lambda: True
sys.modules.setdefault('mainThread', main_thread_stub)

from smartnet.constants import ControllerFunction
from smartnet.message import Message
from smartnet.message_log import (
    CRC16, MLCDataParser, LogEntry, MessageLogReader,
    OP_STATUS, OP_MESSAGE1, OP_MESSAGE2, OP_MESSAGE3
)


class TestCRC16(unittest.TestCase):
    """Test CRC16 CCITT implementation"""
    
    def test_crc16_empty(self):
        """Test CRC of empty data"""
        crc = CRC16.calc(b'')
        # Empty data should give initial CRC value
        self.assertEqual(crc, 0xFFFF)
    
    def test_crc16_single_byte(self):
        """Test CRC of single byte"""
        crc = CRC16.calc(b'\x00')
        # Single zero byte
        self.assertIsInstance(crc, int)
        self.assertGreaterEqual(crc, 0)
        self.assertLessEqual(crc, 0xFFFF)
    
    def test_crc16_known_vector(self):
        """Test against known test vector (if available from controller)"""
        # Using common CCITT test vector: "123456789"
        data = b'123456789'
        crc = CRC16.calc(data)
        # CCITT should give 0x29B1
        self.assertEqual(crc, 0x29B1)
    
    def test_crc16_incremental(self):
        """Test incremental CRC calculation matches batch calculation"""
        data = b'hello'
        
        # Batch calculation
        batch_crc = CRC16.calc(data)
        
        # Incremental calculation
        crc = CRC16()
        for byte in data:
            crc.add_byte(byte)
        incremental_crc = crc.get()
        
        self.assertEqual(batch_crc, incremental_crc)
    
    def test_crc16_different_data(self):
        """Test that different data produces different CRCs"""
        crc1 = CRC16.calc(b'data1')
        crc2 = CRC16.calc(b'data2')
        self.assertNotEqual(crc1, crc2)
    
    def test_crc16_nibble_processing(self):
        """Test correct nibble processing"""
        crc = CRC16()
        # Test byte 0xFF (both nibbles 0x0F)
        crc.add_byte(0xFF)
        result = crc.get()
        # Should be different from initial value
        self.assertNotEqual(result, 0xFFFF)


class TestMLCDataParser(unittest.TestCase):
    """Test MLCData message packing and unpacking"""
    
    def test_pack_status(self):
        """Test packing a STATUS message"""
        timestamp = 0x12345678
        crc16_value = 0x29B1
        
        data = MLCDataParser.pack_status(timestamp, crc16_value)
        
        # Check length
        self.assertEqual(len(data), 8)
        
        # Check operation code
        self.assertEqual(MLCDataParser.parse_operation(data[0]), OP_STATUS)
        
        # Byte 1 is the byte-count field; CRC and timestamp follow it.
        self.assertEqual(data[1], 0)
        unpacked_crc = struct.unpack_from('<H', data, 2)[0]
        unpacked_ts = struct.unpack_from('<I', data, 4)[0]
        
        self.assertEqual(unpacked_crc, crc16_value)
        self.assertEqual(unpacked_ts, timestamp)
    
    def test_unpack_status(self):
        """Test unpacking a STATUS message"""
        # Create a manual STATUS message
        data = bytearray(8)
        data[0] = OP_STATUS
        data[1:3] = struct.pack('<H', 0x29B1)
        data[3:7] = struct.pack('<I', 0x12345678)
        
        timestamp, crc16_value = MLCDataParser.unpack_status(data)
        
        self.assertEqual(timestamp, 0x12345678)
        self.assertEqual(crc16_value, 0x29B1)
    
    def test_unpack_status_wrong_op(self):
        """Test unpacking status with wrong operation code"""
        data = bytearray(8)
        data[0] = MLCDataParser.pack_operation_byte(OP_MESSAGE1)  # Wrong operation
        
        timestamp, crc16_value = MLCDataParser.unpack_status(data)
        
        self.assertIsNone(timestamp)
        self.assertIsNone(crc16_value)
    
    def test_unpack_message1(self):
        """Test unpacking a MESSAGE1 message"""
        data = bytearray(8)
        data[0] = MLCDataParser.pack_operation_byte(OP_MESSAGE1)
        data[1] = 0x02  # severity
        data[2:4] = struct.pack('<H', 0x29B1)
        data[4:8] = struct.pack('<I', 0x12345678)
        
        timestamp, severity, crc16_value = MLCDataParser.unpack_message1(data)
        
        self.assertEqual(timestamp, 0x12345678)
        self.assertEqual(severity, 0x02)
        self.assertEqual(crc16_value, 0x29B1)
    
    def test_unpack_message2(self):
        """Test unpacking a MESSAGE2 message"""
        data = bytearray(8)
        data[0] = MLCDataParser.pack_operation_byte(OP_MESSAGE2)
        data[1] = 0x12  # code
        data[2] = 0xAA  # param_ex0
        data[3] = 0xBB  # param_ex1
        data[4:8] = struct.pack('<I', 0x56789ABC)  # param
        
        code, param, (param_ex0, param_ex1) = MLCDataParser.unpack_message2(data)
        
        self.assertEqual(code, 0x12)
        self.assertEqual(param_ex0, 0xAA)
        self.assertEqual(param_ex1, 0xBB)
    
    def test_unpack_message3(self):
        """Test unpacking a MESSAGE3 message"""
        data = bytearray(8)
        data[0] = MLCDataParser.pack_operation_byte(OP_MESSAGE3)
        data[1:7] = b'\x11\x22\x33\x44\x55\x66'
        
        param_ex = MLCDataParser.unpack_message3(data)
        
        self.assertEqual(param_ex, b'\x11\x22\x33\x44\x55\x66')
    
    def test_parse_operation(self):
        """Test operation code extraction"""
        # Test all operation codes
        self.assertEqual(MLCDataParser.parse_operation(0x00), OP_STATUS)
        self.assertEqual(MLCDataParser.parse_operation(MLCDataParser.pack_operation_byte(OP_MESSAGE1)), OP_MESSAGE1)
        self.assertEqual(MLCDataParser.parse_operation(MLCDataParser.pack_operation_byte(OP_MESSAGE2)), OP_MESSAGE2)
        self.assertEqual(MLCDataParser.parse_operation(MLCDataParser.pack_operation_byte(OP_MESSAGE3)), OP_MESSAGE3)
        
        # Test with byte-count bits set in the packed first byte
        self.assertEqual(
            MLCDataParser.parse_operation(MLCDataParser.pack_operation_byte(OP_STATUS, 0x1F)),
            OP_STATUS,
        )
        self.assertEqual(
            MLCDataParser.parse_operation(MLCDataParser.pack_operation_byte(OP_MESSAGE1, 0x1F)),
            OP_MESSAGE1,
        )


class TestLogEntry(unittest.TestCase):
    """Test LogEntry class"""
    
    def test_log_entry_creation(self):
        """Test creating a log entry"""
        entry = LogEntry()
        
        self.assertEqual(entry.timestamp, 0)
        self.assertEqual(entry.severity, 0)
        self.assertEqual(entry.code, 0)
        self.assertEqual(entry.param, 0)
        self.assertEqual(len(entry.param_ex), 8)
        self.assertEqual(entry.crc16, 0)
    
    def test_log_entry_repr(self):
        """Test string representation"""
        entry = LogEntry()
        entry.timestamp = 1000
        entry.severity = 2
        entry.code = 100
        entry.param = 200
        entry.crc16 = 0x29B1
        
        repr_str = repr(entry)
        
        self.assertIn('timestamp=1000', repr_str)
        self.assertIn('severity=2', repr_str)
        self.assertIn('code=100', repr_str)
        self.assertIn('param=200', repr_str)
        self.assertIn('0x29b1', repr_str.lower())


class TestMessageLogReader(unittest.TestCase):
    """Test MessageLogReader class"""
    
    def setUp(self):
        """Set up test reader"""
        self.reader = MessageLogReader(controller_id=1, timeout=10)
    
    def test_reader_initialization(self):
        """Test reader initialization"""
        self.assertEqual(self.reader.controller_id, 1)
        self.assertEqual(self.reader.FUNCTION_ID, ControllerFunction['JOURNAL'])
        self.assertEqual(self.reader.timeout, 10)
        self.assertEqual(len(self.reader.entries), 0)
    
    def test_calc_entry_crc_simple(self):
        """Test CRC calculation for an entry"""
        entry = LogEntry()
        entry.timestamp = 0x12345678
        entry.severity = 0x01
        entry.code = 0x34
        entry.param = 0x56789ABC
        entry.param_ex[0] = 0x11
        entry.param_ex[1] = 0x22
        entry.param_ex[2] = 0x33
        entry.param_ex[3] = 0x44
        entry.param_ex[4] = 0x55
        entry.param_ex[5] = 0x66
        entry.param_ex[6] = 0x77
        entry.param_ex[7] = 0x88
        
        crc = MessageLogReader._calc_entry_crc(entry)
        
        # CRC should be a valid 16-bit value
        self.assertIsInstance(crc, int)
        self.assertGreaterEqual(crc, 0)
        self.assertLessEqual(crc, 0xFFFF)
    
    def test_calc_entry_crc_deterministic(self):
        """Test that CRC calculation is deterministic"""
        entry = LogEntry()
        entry.timestamp = 0x12345678
        entry.severity = 0x01
        entry.code = 0x34
        entry.param = 0x56789ABC
        entry.param_ex = bytearray(8)
        
        crc1 = MessageLogReader._calc_entry_crc(entry)
        crc2 = MessageLogReader._calc_entry_crc(entry)
        
        self.assertEqual(crc1, crc2)
    
    def test_get_entries(self):
        """Test getting entries list"""
        self.assertEqual(len(self.reader.get_entries()), 0)
    
    def test_clear_entries(self):
        """Test clearing entries"""
        entry = LogEntry()
        self.reader.entries.append(entry)
        
        self.assertEqual(len(self.reader.entries), 1)
        
        self.reader.clear()
        
        self.assertEqual(len(self.reader.entries), 0)
        self.assertIsNone(self.reader._last_entry)


class TestMessageLogIntegration(unittest.TestCase):
    """Integration tests for message log reading"""
    
    def test_entry_crc_validation_cycle(self):
        """Test a complete entry creation and validation cycle"""
        # Create an entry
        entry = LogEntry()
        entry.timestamp = 12345
        entry.severity = 1
        entry.code = 100
        entry.param = 999
        entry.param_ex = bytearray([1, 2, 3, 4, 5, 6, 7, 8])
        
        # Calculate and set CRC
        entry.crc16 = MessageLogReader._calc_entry_crc(entry)
        
        # Validate the CRC matches
        calculated_crc = MessageLogReader._calc_entry_crc(entry)
        self.assertEqual(entry.crc16, calculated_crc)
    
    def test_crc_changes_with_entry_data(self):
        """Test that CRC changes when entry data changes"""
        entry1 = LogEntry()
        entry1.timestamp = 100
        entry1.code = 50
        crc1 = MessageLogReader._calc_entry_crc(entry1)
        
        entry2 = LogEntry()
        entry2.timestamp = 100
        entry2.code = 60  # Different code
        crc2 = MessageLogReader._calc_entry_crc(entry2)
        
        self.assertNotEqual(crc1, crc2)
    
    def test_message_packing_layout(self):
        """Test the controller-compatible STATUS message layout"""
        timestamp = 0x12345678
        crc16_value = 0x29B1
        
        # Pack
        packed = MLCDataParser.pack_status(timestamp, crc16_value)
        
        # Verify CRC and timestamp occupy bytes 2..3 and 4..7.
        self.assertEqual(struct.unpack_from('<H', packed, 2)[0], crc16_value)
        self.assertEqual(struct.unpack_from('<I', packed, 4)[0], timestamp)


class TestJournalTrace(unittest.TestCase):
    def test_trace_records_attempt_and_matching_response_without_changing_frames(self):
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), \
                patch('smartnet.message_log.CanListener.subscribe'), \
                patch('smartnet.message_log.CanListener.unsubscribe'), \
                patch('smartnet.message_log.print_log') as log, \
                patch.object(Message, 'send') as send:
            reader = MessageLogReader(controller_id=123, timeout=1)
            reader._start_capture(123)
            try:
                reader.request_log()
                other = Message(reader.PROGRAM_TYPE, 124, reader.FUNCTION_ID,
                                reader.RESPONSE_FLAG, bytes(8))
                response = Message(reader.PROGRAM_TYPE, 123, reader.FUNCTION_ID,
                                   reader.RESPONSE_FLAG, bytes.fromhex('60 01 02 03 04 05 06 00'))
                reader.on_can_message_received(other)
                reader.on_can_message_received(response)
                self.assertIs(reader._captured_messages.popleft(), response)
                self.assertEqual(len(reader._captured_messages), 0)
            finally:
                reader._stop_capture()
            send.assert_called_once_with()
            lines = [call.args[0] for call in log.call_args_list]
            self.assertEqual(len(lines), 3)
            self.assertIn('TX_ATTEMPT', lines[0])
            self.assertIn('dlc=8 data=00 00 00 00 00 00 00 00', lines[0])
            self.assertIn(f'RX_UNMATCHED id={other.generateHeader():08X}', lines[1])
            self.assertIn(f'RX id={response.generateHeader():08X}', lines[2])
            self.assertIn('dlc=8 data=60 01 02 03 04 05 06 00', lines[2])

    def test_trace_disabled_by_default(self):
        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '0'}), \
                patch('smartnet.message_log.CanListener.subscribe'), \
                patch('smartnet.message_log.CanListener.unsubscribe'), \
                patch('smartnet.message_log.print_log') as log, \
                patch.object(Message, 'send'):
            reader = MessageLogReader(controller_id=123)
            reader.request_log()
            log.assert_not_called()

    def test_trace_complete_exchange_with_two_entries(self):
        entries = []
        for timestamp, code in ((0x12345678, 4), (0x12345679, 5)):
            entry = LogEntry()
            entry.timestamp = timestamp
            entry.severity = 2
            entry.code = code
            entry.param = 101
            entry.param_ex = bytearray(range(8))
            entry.crc16 = MessageLogReader._calc_entry_crc(entry)
            entries.append(entry)

        with patch.dict('os.environ', {'BRS_JOURNAL_TRACE': '1'}), \
                patch('smartnet.message_log.CanListener.subscribe'), \
                patch('smartnet.message_log.CanListener.unsubscribe'), \
                patch('smartnet.message_log.print_log') as log:
            reader = MessageLogReader(controller_id=123, timeout=0.02)
            requests = []

            def send_request(message):
                requests.append(bytes(message.get_data()))
                index = len(requests) - 1
                if index == len(entries):
                    payloads = [MLCDataParser.pack_status(entries[-1].timestamp, entries[-1].crc16)]
                else:
                    entry = entries[index]
                    payloads = [
                        bytes([0x60]) + bytes(entry.param_ex[2:]) + b'\x00',
                        bytes([0x40, entry.code]) + bytes(entry.param_ex[:2]) + struct.pack('<I', entry.param),
                        bytes([0x20, entry.severity]) + struct.pack('<HI', entry.crc16, entry.timestamp),
                    ]
                for payload in payloads:
                    reader.on_can_message_received(Message(reader.PROGRAM_TYPE, 123,
                        reader.FUNCTION_ID, reader.RESPONSE_FLAG, payload))

            with patch.object(Message, 'send', autospec=True, side_effect=send_request):
                result = reader.read_entries(max_entries=3)
            self.assertEqual([entry.code for entry in result], [4, 5])
            self.assertEqual(requests[0], bytes(8))
            self.assertEqual(requests[1:], [struct.pack('<BBHI', 0, 0, entry.crc16, entry.timestamp)
                                          for entry in entries])
            lines = [call.args[0] for call in log.call_args_list]
            self.assertEqual(sum('TX_ATTEMPT' in line for line in lines), 3)
            self.assertEqual(sum(' RX id=' in line for line in lines), 7)
            self.assertEqual(sum('entry_ok' in line for line in lines), 2)
            self.assertTrue(any('read_end entries=2 limit_reached=False' in line for line in lines))


class TestJournalRetries(unittest.TestCase):
    def run_exchange(self, responses, cursor=None):
        requests = []
        with patch('smartnet.message_log.CanListener.subscribe'), \
                patch('smartnet.message_log.CanListener.unsubscribe'):
            reader = MessageLogReader(controller_id=209, timeout=0.001)

            def send(message):
                requests.append(bytes(message.get_data()))
                index = len(requests) - 1
                for payload in responses[index] if index < len(responses) else []:
                    reader.on_can_message_received(Message(reader.PROGRAM_TYPE, 209,
                        reader.FUNCTION_ID, reader.RESPONSE_FLAG, payload))

            with patch.object(Message, 'send', autospec=True, side_effect=send):
                entries = reader.read_entries(max_entries=10, last_entry=cursor)
        return requests, entries, reader

    def test_silent_request_retries_same_captured_cursor_until_status(self):
        cursor = LogEntry()
        cursor.timestamp = 1793563620
        cursor.severity = 3
        cursor.code = 63
        cursor.param = 123
        requests, entries, reader = self.run_exchange([[], [], [bytes.fromhex('00 00 95 9E E4 9B E7 6A')]], cursor)
        self.assertEqual(requests, [bytes.fromhex('00 00 95 9E E4 9B E7 6A')] * 3)
        self.assertEqual(entries, [])
        self.assertFalse(reader._last_sequence_silent)

    def test_silent_exhaustion_is_not_a_status(self):
        requests, entries, reader = self.run_exchange([[], [], []])
        self.assertEqual(requests, [bytes(8)] * 3)
        self.assertEqual(entries, [])
        self.assertTrue(reader._last_sequence_silent)

    def test_status_is_not_retried(self):
        requests, entries, reader = self.run_exchange([[bytes(8)]])
        self.assertEqual(len(requests), 1)
        self.assertEqual(entries, [])
        self.assertFalse(reader._last_sequence_silent)

    def test_partial_response_is_retried_without_accepting_silence(self):
        requests, entries, reader = self.run_exchange([[bytes.fromhex('60 00 00 00 00 00 00 00')]])
        self.assertEqual(len(requests), 3)
        self.assertEqual(entries, [])
        self.assertTrue(reader._last_sequence_has_chunks)
        self.assertFalse(reader.status_received)

    def test_crc_failure_is_retried_without_accepting_bad_entry(self):
        requests, entries, reader = self.run_exchange([[bytes.fromhex('60 00 00 00 00 00 00 00'),
            bytes.fromhex('40 3F 00 00 7B 00 00 00'),
            bytes.fromhex('20 03 00 00 E4 9B E7 6A')]])
        self.assertEqual(len(requests), 3)
        self.assertEqual(entries, [])
        self.assertTrue(reader._last_sequence_has_chunks)
        self.assertFalse(reader.status_received)

    def test_all_fragment_orders(self):
        frames = [bytes.fromhex('60 00 00 00 00 00 00 00'),
                  bytes.fromhex('40 3F 00 00 7B 00 00 00'),
                  bytes.fromhex('20 03 95 9E E4 9B E7 6A')]
        status = bytes.fromhex('00 00 95 9E E4 9B E7 6A')
        for order in permutations(frames):
            with self.subTest(order=order):
                requests, entries, reader = self.run_exchange([order, [status]])
                self.assertEqual(len(requests), 2)
                self.assertEqual([(entry.code, entry.param, entry.crc16) for entry in entries], [(63, 123, 0x9E95)])
                self.assertTrue(reader.status_received)

    def test_late_fragments_are_combined_across_retry(self):
        requests, entries, reader = self.run_exchange([
            [bytes.fromhex('60 00 00 00 00 00 00 00')],
            [bytes.fromhex('20 03 95 9E E4 9B E7 6A'), bytes.fromhex('40 3F 00 00 7B 00 00 00')],
            [bytes.fromhex('00 00 95 9E E4 9B E7 6A')],
        ])
        self.assertEqual(requests[:2], [bytes(8), bytes(8)])
        self.assertEqual([(entry.code, entry.crc16) for entry in entries], [(63, 0x9E95)])
        self.assertTrue(reader.status_received)

    def test_log_9_11_delayed_fragments(self):
        requests, entries, reader = self.run_exchange([
            [bytes.fromhex('60 00 00 00 00 00 00 00')],
            [bytes.fromhex('40 09 01 01 66 00 00 00'), bytes.fromhex('20 85 81 D3 53 89 E7 6A')],
            [bytes.fromhex('00 00 81 D3 53 89 E7 6A')],
        ])
        self.assertEqual(requests[:2], [bytes(8)] * 2)
        self.assertEqual([(entry.code, entry.param, entry.crc16) for entry in entries], [(9, 102, 0xD381)])
        self.assertTrue(reader.status_received)

    def test_matching_status_before_new_fragments_does_not_hide_entry(self):
        requests, entries, reader = self.run_exchange([
            [bytes(8), bytes.fromhex('60 00 00 00 00 00 00 00'),
             bytes.fromhex('40 3F 00 00 7B 00 00 00'), bytes.fromhex('20 03 95 9E E4 9B E7 6A')],
            [bytes.fromhex('00 00 95 9E E4 9B E7 6A')],
        ])
        self.assertEqual([(entry.code, entry.crc16) for entry in entries], [(63, 0x9E95)])
        self.assertTrue(reader.status_received)

    def test_duplicate_and_orphan_do_not_advance_cursor(self):
        cursor = LogEntry()
        cursor.timestamp, cursor.severity, cursor.code, cursor.param = 1793563620, 3, 63, 123
        requests, entries, reader = self.run_exchange([
            [bytes.fromhex('60 00 00 00 00 00 00 00'), bytes.fromhex('40 3F 00 00 7B 00 00 00'),
             bytes.fromhex('20 03 95 9E E4 9B E7 6A'), bytes.fromhex('60 00 00 00 00 00 00 00')],
            [bytes.fromhex('40 09 00 00 66 00 00 00'), bytes.fromhex('20 85 EF FF 18 A7 E7 6A')],
            [bytes.fromhex('00 00 EF FF 18 A7 E7 6A')],
        ], cursor)
        self.assertEqual(requests[:2], [bytes.fromhex('00 00 95 9E E4 9B E7 6A')] * 2)
        self.assertEqual([(entry.code, entry.crc16) for entry in entries], [(9, 0xFFEF)])
        self.assertTrue(reader.status_received)

    def test_log_9_3_duplicate_fragments_then_status(self):
        cursor = LogEntry()
        cursor.timestamp, cursor.severity, cursor.code, cursor.param = 1793567594, 5, 8, 102
        cursor.param_ex[:2] = bytes.fromhex('D1 66')
        first = bytes.fromhex('20 86 89 A6 6E AB E7 6A')
        second = bytes.fromhex('40 04 66 66 00 00 00 00')
        third = bytes.fromhex('60 00 00 00 00 00 00 00')
        requests, entries, reader = self.run_exchange([
            [third, second, first, third],
            [second, first],
            [bytes.fromhex('00 00 89 A6 6E AB E7 6A')],
        ], cursor)
        self.assertEqual([(entry.timestamp, entry.crc16) for entry in entries], [(1793567598, 0xA689)])
        self.assertEqual(requests[1:], [bytes.fromhex('00 00 89 A6 6E AB E7 6A')] * 2)
        self.assertTrue(reader.status_received)

    def test_status_for_another_cursor_does_not_confirm_end(self):
        cursor = LogEntry()
        cursor.timestamp, cursor.severity, cursor.code, cursor.param = 1793563620, 3, 63, 123
        requests, entries, reader = self.run_exchange([[bytes(8)], [], []], cursor)
        self.assertEqual(len(requests), 3)
        self.assertEqual(entries, [])
        self.assertFalse(reader.status_received)

    def test_selects_crc_valid_combination_from_mixed_fragments(self):
        requests, entries, reader = self.run_exchange([
            [bytes.fromhex('40 09 00 00 66 00 00 00'), bytes.fromhex('20 03 95 9E E4 9B E7 6A'),
             bytes.fromhex('40 3F 00 00 7B 00 00 00'), bytes.fromhex('60 00 00 00 00 00 00 00')],
            [bytes.fromhex('00 00 95 9E E4 9B E7 6A')],
        ])
        self.assertEqual([(entry.code, entry.param, entry.crc16) for entry in entries], [(63, 123, 0x9E95)])
        self.assertTrue(reader.status_received)

    def test_multiple_crc_valid_combinations_fail_closed(self):
        with patch('smartnet.message_log.CanListener.subscribe'), \
                patch('smartnet.message_log.CanListener.unsubscribe'):
            reader = MessageLogReader(controller_id=209, timeout=0.01)
            def send(message):
                for payload in (bytes.fromhex('20 03 95 9E E4 9B E7 6A'),
                                bytes.fromhex('40 3F 00 00 7B 00 00 00'),
                                bytes.fromhex('40 09 00 00 66 00 00 00'),
                                bytes.fromhex('60 00 00 00 00 00 00 00')):
                    reader.on_can_message_received(Message(reader.PROGRAM_TYPE, 209,
                        reader.FUNCTION_ID, reader.RESPONSE_FLAG, payload))
            with patch.object(Message, 'send', autospec=True, side_effect=send), \
                    patch.object(reader, '_calc_entry_crc', return_value=0x9E95):
                self.assertEqual(reader.read_entries(), [])
            self.assertFalse(reader.status_received)
            self.assertTrue(reader._last_sequence_has_chunks)

    def test_fragment_buffer_limit_fails_closed(self):
        payloads = [bytes([0x40, value]) + bytes(6) for value in range(9)]
        requests, entries, reader = self.run_exchange([payloads])
        self.assertEqual(len(requests), 1)
        self.assertEqual(entries, [])
        self.assertFalse(reader.status_received)
        self.assertTrue(reader._last_sequence_has_chunks)


class TestCRC16EdgeCases(unittest.TestCase):
    """Test CRC16 edge cases"""
    
    def test_crc16_all_zeros(self):
        """Test CRC of all zeros"""
        crc = CRC16.calc(b'\x00' * 100)
        self.assertIsInstance(crc, int)
        self.assertLessEqual(crc, 0xFFFF)
    
    def test_crc16_all_ones(self):
        """Test CRC of all ones"""
        crc = CRC16.calc(b'\xFF' * 100)
        self.assertIsInstance(crc, int)
        self.assertLessEqual(crc, 0xFFFF)
    
    def test_crc16_alternating_pattern(self):
        """Test CRC of alternating bit pattern"""
        crc = CRC16.calc(b'\xAA\x55' * 50)
        self.assertIsInstance(crc, int)
        self.assertLessEqual(crc, 0xFFFF)
    
    def test_crc16_long_sequence(self):
        """Test CRC of long sequence"""
        data = bytes(range(256)) * 10
        crc = CRC16.calc(data)
        self.assertIsInstance(crc, int)
        self.assertLessEqual(crc, 0xFFFF)


if __name__ == '__main__':
    unittest.main()
