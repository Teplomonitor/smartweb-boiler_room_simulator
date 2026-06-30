'''
@author: admin
Message Log module for reading error/message log from controller via CAN

Based on MessageLogCan.cc protocol:
- Uses 8-byte CAN messages (MLCData)
- Messages contain operation codes: STATUS, MESSAGE1, MESSAGE2, MESSAGE3
- Each entry is transmitted as 3 consecutive messages (MSG1, MSG2, MSG3)
- CRC16 CCITT is used for integrity verification
'''

import struct
import time
from smartnet.message import Message
from smartnet.constants import ProgramType
from smartnet.constants import ControllerFunction



# Operation codes (stored in bits 0-2 of first byte)
OP_STATUS = 0
OP_MESSAGE1 = 1
OP_MESSAGE2 = 2
OP_MESSAGE3 = 3

# Parse result codes
PR_STATUS_EQUAL = 0
PR_STATUS_NOTEQUAL = 1
PR_MESSAGE = 2
PR_MESSAGE_RECEIVED = 3
PR_MESSAGE_WRONG_CRC = 4


class CRC16:
    """CRC16 CCITT implementation matching the controller's crc16.c"""
    
    # CRC16 Lookup tables for 4-bit processing
    CRC16_LookupHigh = [
        0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
        0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1
    ]
    
    CRC16_LookupLow = [
        0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
        0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF
    ]
    
    def __init__(self):
        self.high = 0xFF
        self.low = 0xFF
    
    def add_byte(self, val):
        """Add one byte to the CRC (processing high and low nibbles)"""
        self._update_4bits(val >> 4)      # High nibble first
        self._update_4bits(val & 0x0F)    # Low nibble
    
    def _update_4bits(self, val):
        """Process 4 bits of message to update CRC"""
        # Extract MSB 4 bits of CRC register
        t = self.high >> 4
        
        # XOR in the message data
        t = t ^ val
        
        # Shift CRC register left 4 bits
        self.high = ((self.high << 4) | (self.low >> 4)) & 0xFF
        self.low = (self.low << 4) & 0xFF
        
        # Do table lookups and XOR result into CRC
        self.high = self.high ^ self.CRC16_LookupHigh[t]
        self.low = self.low ^ self.CRC16_LookupLow[t]
    
    def get(self):
        """Get the calculated CRC value"""
        return ((self.high << 8) | self.low) & 0xFFFF
    
    @staticmethod
    def calc(data):
        """Calculate CRC16 for a byte sequence"""
        crc = CRC16()
        for byte in data:
            crc.add_byte(byte)
        return crc.get()


class LogEntry:
    """Represents a single log entry from the controller"""
    
    def __init__(self):
        self.timestamp = 0          # Unix timestamp
        self.severity = 0           # Message severity
        self.code = 0               # Error/message code
        self.param = 0              # Parameter value
        self.param_ex = bytearray(8)  # Extended parameters
        self.crc16 = 0              # CRC for validation
    
    def __repr__(self):
        return (f"LogEntry(timestamp={self.timestamp}, severity={self.severity}, "
                f"code={self.code}, param={self.param}, crc16=0x{self.crc16:04X})")


class MLCDataParser:
    """Parser for MLCData 8-byte messages"""
    
    @staticmethod
    def parse_operation(byte0):
        """Extract operation code from first byte"""
        return byte0 & 0x07
    
    @staticmethod
    def pack_status(timestamp, crc16_value):
        """Pack a STATUS message"""
        data = bytearray(8)
        data[0] = OP_STATUS
        data[1:3] = struct.pack('<H', crc16_value)
        data[3:7] = struct.pack('<I', timestamp)
        return bytes(data)
    
    @staticmethod
    def unpack_status(data):
        """Unpack a STATUS message"""
        if len(data) < 7:
            return None, None
        op = data[0] & 0x07
        if op != OP_STATUS:
            return None, None
        crc16_value = struct.unpack_from('<H', data, 1)[0]
        timestamp = struct.unpack_from('<I', data, 3)[0]
        return timestamp, crc16_value
    
    @staticmethod
    def unpack_message1(data):
        """Unpack a MESSAGE1 message"""
        if len(data) < 7:
            return None, None, None
        op = data[0] & 0x07
        if op != OP_MESSAGE1:
            return None, None, None
        severity = data[1]
        crc16_value = struct.unpack_from('<H', data, 2)[0]
        timestamp = struct.unpack_from('<I', data, 4)[0]
        return timestamp, severity, crc16_value
    
    @staticmethod
    def unpack_message2(data):
        """Unpack a MESSAGE2 message"""
        if len(data) < 8:
            return None, None, None, None
        op = data[0] & 0x07
        if op != OP_MESSAGE2:
            return None, None, None, None
        code = struct.unpack_from('<H', data, 1)[0]
        param_ex0 = data[3]
        param_ex1 = data[4]
        param = struct.unpack_from('<I', data, 5)[0]
        return code, param, (param_ex0, param_ex1)
    
    @staticmethod
    def unpack_message3(data):
        """Unpack a MESSAGE3 message"""
        if len(data) < 7:
            return None
        op = data[0] & 0x07
        if op != OP_MESSAGE3:
            return None
        param_ex = data[1:7]
        return param_ex


class MessageLogReader:
    """Reads and parses error log messages from the controller"""
    
    # Default program IDs for message log communication
    PROGRAM_TYPE  = ProgramType['CONTROLLER']        # Controller
    FUNCTION_ID   = ControllerFunction['JOURNAL']    # JOURNAL function
    REQUEST_FLAG  = 0x00        # Request (0x00) vs Response (0x01)
    RESPONSE_FLAG = 0x01
    
    def __init__(self, program_id=0, timeout=10):
        """
        Initialize the message log reader
        
        Args:
            program_id: Controller program ID
            timeout: Timeout in seconds for reading entries
        """
        self.program_id = program_id
        self.timeout = timeout
        self.entries = []
        self._last_entry = None
    
    def request_log(self, program_id=None):
        """
        Send a request to read the message log from the controller
        
        Args:
            program_id: Controller program ID (uses default if None)
            
        Returns:
            True if request sent successfully, False otherwise
        """
        if program_id is None:
            program_id = self.program_id
        
        # Create status request message
        if self._last_entry:
            # If we have a previous entry, send its CRC and timestamp
            crc = self._calc_entry_crc(self._last_entry)
            timestamp = self._last_entry.timestamp
        else:
            # First request: use zero values
            crc = 0
            timestamp = 0
        
        request_data = MLCDataParser.pack_status(timestamp, crc)
        
        # Create and send CAN message
        msg = Message(
            programType=self.PROGRAM_TYPE,
            programId=program_id,
            functionId=self.FUNCTION_ID,
            request=self.REQUEST_FLAG,
            data=request_data
        )
        
        # Send request and wait for response
        response_filter = Message(
            programType=self.PROGRAM_TYPE,
            programId=program_id,
            functionId=self.FUNCTION_ID,
            request=self.RESPONSE_FLAG
        )
        
        response = msg.send(responseFilter=response_filter, timeout=self.timeout)
        return response is not None
    
    def read_entries(self, program_id=None, max_entries=100):
        """
        Read all available log entries from the controller
        
        Args:
            program_id: Controller program ID (uses default if None)
            max_entries: Maximum number of entries to read
            
        Returns:
            List of LogEntry objects
        """
        if program_id is None:
            program_id = self.program_id
        
        # Use the fixed class-level FUNCTION_ID for journal function
        function_id = self.FUNCTION_ID
        
        self.entries = []
        entries_read = 0
        
        while entries_read < max_entries:
            # Send request (request_log uses program_id and class FUNCTION_ID)
            if not self.request_log(program_id):
                break
            
            # Try to read MESSAGE1/2/3 sequence
            entry = self._read_entry_sequence(program_id)
            if entry is None:
                break
            
            self.entries.append(entry)
            self._last_entry = entry
            entries_read += 1
        
        return self.entries
    
    def _read_entry_sequence(self, program_id):
        """
        Read a single entry (MESSAGE1/MESSAGE2/MESSAGE3 sequence)
        
        Returns:
            LogEntry if successful, None if failed or no new entries
        """
        entry = LogEntry()
        start_time = time.time()
        messages = {}  # Store messages by operation type
        
        # Collect up to 3 messages (MESSAGE1, MESSAGE2, MESSAGE3)
        while len(messages) < 3 and (time.time() - start_time) < self.timeout:
            response_filter = Message(
                programType=self.PROGRAM_TYPE,
                programId=program_id,
                functionId=self.FUNCTION_ID,
                request=self.RESPONSE_FLAG
            )
            
            # Create dummy message to use recv method
            dummy_msg = Message(
                programType=self.PROGRAM_TYPE,
                programId=program_id,
                functionId=self.FUNCTION_ID,
                request=self.REQUEST_FLAG
            )
            
            response = dummy_msg.recv(responseFilter=response_filter, timeout=2)
            
            if response is None:
                break
            
            # Parse the response
            op = MLCDataParser.parse_operation(response.get_data()[0])
            
            if op == OP_STATUS:
                # Got status instead of message data - no new entries
                return None
            elif op == OP_MESSAGE1:
                timestamp, severity, crc16_value = MLCDataParser.unpack_message1(response.get_data())
                if timestamp is not None:
                    entry.timestamp = timestamp
                    entry.severity = severity
                    entry.crc16 = crc16_value
                    messages[OP_MESSAGE1] = True
            elif op == OP_MESSAGE2:
                code, param, (param_ex0, param_ex1) = MLCDataParser.unpack_message2(response.get_data())
                if code is not None:
                    entry.code = code
                    entry.param = param
                    entry.param_ex[0] = param_ex0
                    entry.param_ex[1] = param_ex1
                    messages[OP_MESSAGE2] = True
            elif op == OP_MESSAGE3:
                param_ex = MLCDataParser.unpack_message3(response.get_data())
                if param_ex is not None:
                    entry.param_ex[2:8] = param_ex
                    messages[OP_MESSAGE3] = True
        
        # Check if we got all required messages
        if OP_MESSAGE1 not in messages or OP_MESSAGE2 not in messages or OP_MESSAGE3 not in messages:
            return None
        
        # Verify CRC
        calculated_crc = self._calc_entry_crc(entry)
        if calculated_crc != entry.crc16:
            return None  # CRC mismatch
        
        return entry
    
    @staticmethod
    def _calc_entry_crc(entry):
        """Calculate CRC16 for a log entry"""
        crc = CRC16()
        
        # Add timestamp (4 bytes, little-endian)
        timestamp_bytes = struct.pack('<I', entry.timestamp)
        for byte in timestamp_bytes:
            crc.add_byte(byte)
        
        # Add severity (1 byte)
        crc.add_byte(entry.severity)
        
        # Add code (2 bytes, little-endian)
        code_bytes = struct.pack('<H', entry.code)
        for byte in code_bytes:
            crc.add_byte(byte)
        
        # Add param (4 bytes, little-endian)
        param_bytes = struct.pack('<I', entry.param)
        for byte in param_bytes:
            crc.add_byte(byte)
        
        # Add param_ex (8 bytes)
        for byte in entry.param_ex:
            crc.add_byte(byte)
        
        return crc.get()
    
    def get_entries(self):
        """Get the list of read entries"""
        return self.entries
    
    def clear(self):
        """Clear the entries list"""
        self.entries = []
        self._last_entry = None
