'''
@author: admin
Message Log module for reading error/message log from controller via CAN

Based on MessageLogCan.cc protocol:
- Uses 8-byte CAN messages (MLCData)
- Messages contain operation codes: STATUS, MESSAGE1, MESSAGE2, MESSAGE3
- Each entry is transmitted as 3 consecutive messages (MSG1, MSG2, MSG3)
- CRC16 CCITT is used for integrity verification
'''

import os
import struct
import time
import threading
from collections import deque
from itertools import product
from consoleLog import print_log
from smartnet.message import Message
from smartnet.message import CanListener
from smartnet.constants import RequestFlag
from smartnet.constants import ProgramType
from smartnet.constants import ControllerFunction
from smartnet.crc16 import CRC16



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
        return (byte0 >> 5) & 0x07
    
    @staticmethod
    def pack_operation_byte(status, bytes_num = 0):
        return (status << 5) | (bytes_num & 0x1F)
    
    @staticmethod
    def pack_status(timestamp, crc16_value):
        """Pack a STATUS message"""
        data = bytearray(8)
        data[0] = MLCDataParser.pack_operation_byte(OP_STATUS)
        data[2:4] = struct.pack('<H', crc16_value)
        data[4:8] = struct.pack('<I', timestamp)
        return bytes(data)
    
    @staticmethod
    def unpack_status(data):
        """Unpack a STATUS message"""
        if len(data) < 7:
            return None, None
        op = MLCDataParser.parse_operation(data[0])
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
        op = MLCDataParser.parse_operation(data[0])
        if op != OP_MESSAGE1:
            return None, None, None
           
        MESSAGE_SEVERITY_EXCLUDE_IGNORE_MASK = 0x7F
        severity = data[1] & MESSAGE_SEVERITY_EXCLUDE_IGNORE_MASK
        crc16_value = struct.unpack_from('<H', data, 2)[0]
        timestamp = struct.unpack_from('<I', data, 4)[0]
        return timestamp, severity, crc16_value
    
    @staticmethod
    def unpack_message2(data):
        """Unpack a MESSAGE2 message"""
        if len(data) < 8:
            return None, None, None, None
        op = MLCDataParser.parse_operation(data[0])
        if op != OP_MESSAGE2:
            return None, None, None, None
        code = data[1]
        param_ex0 = data[2]
        param_ex1 = data[3]
        param = struct.unpack_from('<I', data, 4)[0]
        return code, param, (param_ex0, param_ex1)
    
    @staticmethod
    def unpack_message3(data):
        """Unpack a MESSAGE3 message"""
        if len(data) < 7:
            return None
        op = MLCDataParser.parse_operation(data[0])
        if op != OP_MESSAGE3:
            return None
        param_ex = data[1:7]
        return param_ex


class MessageLogReader:
    """Reads and parses error log messages from the controller"""

    INCOMPLETE_REQUEST_RETRIES = 2
    MAX_FRAGMENT_CANDIDATES = 8
    
    # Default program IDs for message log communication
    PROGRAM_TYPE  = ProgramType.CONTROLLER             # Controller
    FUNCTION_ID   = ControllerFunction['JOURNAL']    # JOURNAL function
    REQUEST_FLAG  = RequestFlag['REQUEST']        # Request (0x00) vs Response (0x10)
    RESPONSE_FLAG = RequestFlag['RESPONSE']
    
    def __init__(self, controller_id=0, timeout=100):
        """
        Initialize the message log reader
        
        Args:
            controller_id: Controller program ID
            timeout: Timeout in seconds for reading entries
        """
        self.controller_id = controller_id
        self.timeout = timeout
        self.entries = []
        self._last_entry = None
        self._response_filter = None
        self._captured_messages = deque()
        self._capture_lock = threading.Lock()
        self._last_sequence_silent = False
        self._last_sequence_has_chunks = False
        self.status_received = False
        self._trace_enabled = os.environ.get('BRS_JOURNAL_TRACE') == '1'
        CanListener.subscribe(self)

    def _trace(self, message):
        if self._trace_enabled:
            print_log(f'JOURNAL_TRACE time={time.time():.6f} {message}')

    def _trace_frame(self, direction, msg):
        if self._trace_enabled:
            data = msg.get_data()
            payload = bytes(data) if data is not None else b''
            self._trace(f'{direction} id={msg.generateHeader():08X} dlc={len(payload)} '
                        f'data={payload.hex(" ").upper()}')
    
    def __del__(self):
        CanListener.unsubscribe(self)
        
    def on_can_message_received(self, msg):
        if msg is None:
            return

        with self._capture_lock:
            response_filter = self._response_filter

        if response_filter is None:
            return

        if not msg.compare(response_filter):
            if (self._trace_enabled and msg.get_program_type() == self.PROGRAM_TYPE
                    and msg.getFunctionId() == self.FUNCTION_ID
                    and msg.getRequestFlag() == self.RESPONSE_FLAG):
                self._trace_frame('RX_UNMATCHED', msg)
            return

        with self._capture_lock:
            # Append only while the same capture session is active.
            if self._response_filter is response_filter:
                self._captured_messages.append(msg)
            else:
                return
        self._trace_frame('RX', msg)

    def _build_response_filter(self, controller_id):
        return Message(
            programType=self.PROGRAM_TYPE,
            programId=controller_id,
            functionId=self.FUNCTION_ID,
            request=self.RESPONSE_FLAG
        )

    def _start_capture(self, controller_id):
        with self._capture_lock:
            self._response_filter = self._build_response_filter(controller_id)
            self._captured_messages.clear()

    def _stop_capture(self):
        with self._capture_lock:
            self._response_filter = None
            self._captured_messages.clear()

    def _pop_captured_message(self, deadline):
        while time.monotonic() < deadline:
            with self._capture_lock:
                if self._captured_messages:
                    return self._captured_messages.popleft()
            time.sleep(0.01)
        return None
            
    def request_log(self, controller_id=None):
        """
        Send a request to read the message log from the controller
        
        Args:
            controller_id: Controller program ID (uses default if None)
            
        Returns:
            True if request sent successfully, False otherwise
        """
        if controller_id is None:
            controller_id = self.controller_id
        
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
            programId=controller_id,
            functionId=self.FUNCTION_ID,
            request=self.REQUEST_FLAG,
            data=request_data
        )

        self._trace_frame('TX_ATTEMPT', msg)
        msg.send()
    
    def read_entries(self, controller_id=None, max_entries=100, last_entry = None):
        """
        Read all available log entries from the controller
        
        Args:
            controller_id: Controller program ID (uses default if None)
            max_entries: Maximum number of entries to read
            
        Returns:
            List of LogEntry objects
        """
        if controller_id is None:
            controller_id = self.controller_id
        
        self.entries = []
        entries_read = 0
        
        if last_entry:
            self._last_entry = last_entry

        self._trace(f'read_start controller={controller_id} max_entries={max_entries} '
                    f'cursor={self._last_entry!r}')
        self._start_capture(controller_id)
        try:
            while entries_read < max_entries:
                entry = self._read_entry_sequence(controller_id)
                if entry is None:
                    break

                self.entries.append(entry)
                self._last_entry = entry
                entries_read += 1
        finally:
            self._stop_capture()
            self._trace(f'read_end entries={entries_read} limit_reached={entries_read >= max_entries}')
        
        return self.entries
    
    def _read_entry_sequence(self, controller_id):
        """
        Read a single entry (MESSAGE1/MESSAGE2/MESSAGE3 sequence)
        
        Returns:
            LogEntry if successful, None if failed or no new entries
        """
        fragments = {OP_MESSAGE1: [], OP_MESSAGE2: [], OP_MESSAGE3: []}
        cursor_crc = self._calc_entry_crc(self._last_entry) if self._last_entry else 0
        cursor_timestamp = self._last_entry.timestamp if self._last_entry else 0
        expected_status = MLCDataParser.pack_status(cursor_timestamp, cursor_crc)
        self.status_received = False

        for attempt in range(self.INCOMPLETE_REQUEST_RETRIES + 1):
            self._last_sequence_silent = True
            saw_fragment = False
            matching_status = False
            self.request_log(controller_id)
            deadline = time.monotonic() + self.timeout
            while time.monotonic() < deadline:
                response = self._pop_captured_message(deadline)
                if response is None:
                    break
                self._last_sequence_silent = False
                data = bytes(response.get_data() or b'')
                if not data:
                    continue
                op = MLCDataParser.parse_operation(data[0])
                if op == OP_STATUS:
                    # The legacy wire layout has a padding byte at offset 1.
                    if len(data) == 8 and data[2:8] == expected_status[2:8]:
                        matching_status = True
                    continue
                if op not in fragments or len(data) != 8:
                    continue
                saw_fragment = True
                if data not in fragments[op]:
                    if len(fragments[op]) >= self.MAX_FRAGMENT_CANDIDATES:
                        self._trace(f'fragment_limit op={op}')
                        self._last_sequence_has_chunks = True
                        return None
                    fragments[op].append(data)

                matches = {}
                duplicate_headers = set()
                for first, second, third in product(fragments[OP_MESSAGE1],
                                                     fragments[OP_MESSAGE2], fragments[OP_MESSAGE3]):
                    entry = LogEntry()
                    entry.timestamp, entry.severity, entry.crc16 = MLCDataParser.unpack_message1(first)
                    entry.code, entry.param, param_ex = MLCDataParser.unpack_message2(second)
                    entry.param_ex[:2] = bytes(param_ex)
                    entry.param_ex[2:] = MLCDataParser.unpack_message3(third)
                    if self._calc_entry_crc(entry) != entry.crc16:
                        continue
                    if self._last_entry and (entry.timestamp, entry.crc16) == (cursor_timestamp, cursor_crc):
                        duplicate_headers.add(first)
                        continue
                    key = (entry.timestamp, entry.severity, entry.code, entry.param, bytes(entry.param_ex))
                    matches[key] = entry
                for first in duplicate_headers:
                    fragments[OP_MESSAGE1].remove(first)
                    self._trace('duplicate_entry ignored')
                if len(matches) > 1:
                    self._trace('ambiguous_entry multiple CRC-valid combinations')
                    self._last_sequence_has_chunks = True
                    return None
                if matches:
                    entry = next(iter(matches.values()))
                    self._last_sequence_has_chunks = True
                    self._trace(f'entry_ok {entry!r} param_ex={bytes(entry.param_ex).hex(" ").upper()}')
                    return entry

            # A matching STATUS confirms the cursor only when no potentially new
            # record header remains. Retry once more if this attempt had fragments.
            if matching_status and not saw_fragment and not fragments[OP_MESSAGE1]:
                self.status_received = True
                self._last_sequence_has_chunks = False
                return None
            self._last_sequence_has_chunks = any(fragments.values())
            self._trace(f'incomplete_entry chunks={[op for op, values in fragments.items() if values]}')
            if attempt < self.INCOMPLETE_REQUEST_RETRIES:
                self._trace(f'retry_incomplete attempt={attempt + 2} cursor={self._last_entry!r}')
        return None
    
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
        
        # Add code (1 byte)
        crc.add_byte(entry.code)
        
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
