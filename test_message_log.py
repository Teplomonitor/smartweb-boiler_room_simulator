'''
Unit tests for the Message Log module

Tests CRC16 calculation, message packing/unpacking, and entry creation
'''

import unittest
import struct
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
        self.assertEqual(data[0] & 0x07, OP_STATUS)
        
        # Check CRC and timestamp are present
        unpacked_crc = struct.unpack_from('<H', data, 1)[0]
        unpacked_ts = struct.unpack_from('<I', data, 3)[0]
        
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
        data[0] = OP_MESSAGE1  # Wrong operation
        
        timestamp, crc16_value = MLCDataParser.unpack_status(data)
        
        self.assertIsNone(timestamp)
        self.assertIsNone(crc16_value)
    
    def test_unpack_message1(self):
        """Test unpacking a MESSAGE1 message"""
        data = bytearray(8)
        data[0] = OP_MESSAGE1
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
        data[0] = OP_MESSAGE2
        data[1:3] = struct.pack('<H', 0x1234)  # code
        data[3] = 0xAA  # param_ex0
        data[4] = 0xBB  # param_ex1
        data[5:9] = struct.pack('<I', 0x56789ABC)  # param (but only 3 bytes fit)
        
        code, param, (param_ex0, param_ex1) = MLCDataParser.unpack_message2(data)
        
        self.assertEqual(code, 0x1234)
        self.assertEqual(param_ex0, 0xAA)
        self.assertEqual(param_ex1, 0xBB)
    
    def test_unpack_message3(self):
        """Test unpacking a MESSAGE3 message"""
        data = bytearray(8)
        data[0] = OP_MESSAGE3
        data[1:7] = b'\x11\x22\x33\x44\x55\x66'
        
        param_ex = MLCDataParser.unpack_message3(data)
        
        self.assertEqual(param_ex, b'\x11\x22\x33\x44\x55\x66')
    
    def test_parse_operation(self):
        """Test operation code extraction"""
        # Test all operation codes
        self.assertEqual(MLCDataParser.parse_operation(0x00), OP_STATUS)
        self.assertEqual(MLCDataParser.parse_operation(0x01), OP_MESSAGE1)
        self.assertEqual(MLCDataParser.parse_operation(0x02), OP_MESSAGE2)
        self.assertEqual(MLCDataParser.parse_operation(0x03), OP_MESSAGE3)
        
        # Test with number bits set
        self.assertEqual(MLCDataParser.parse_operation(0xF8), OP_STATUS)
        self.assertEqual(MLCDataParser.parse_operation(0xF9), OP_MESSAGE1)


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
        self.reader = MessageLogReader(program_id=1, function_id=0)
    
    def test_reader_initialization(self):
        """Test reader initialization"""
        self.assertEqual(self.reader.program_id, 1)
        self.assertEqual(self.reader.function_id, 0)
        self.assertEqual(self.reader.timeout, 10)
        self.assertEqual(len(self.reader.entries), 0)
    
    def test_calc_entry_crc_simple(self):
        """Test CRC calculation for an entry"""
        entry = LogEntry()
        entry.timestamp = 0x12345678
        entry.severity = 0x01
        entry.code = 0x1234
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
        entry.code = 0x1234
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
    
    def test_message_packing_roundtrip(self):
        """Test packing and unpacking a message"""
        timestamp = 0x12345678
        crc16_value = 0x29B1
        
        # Pack
        packed = MLCDataParser.pack_status(timestamp, crc16_value)
        
        # Unpack
        unpacked_ts, unpacked_crc = MLCDataParser.unpack_status(packed)
        
        # Verify
        self.assertEqual(unpacked_ts, timestamp)
        self.assertEqual(unpacked_crc, crc16_value)


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
