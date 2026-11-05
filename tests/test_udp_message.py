"""Offline checks for the fixed-width CAN-over-UDP wire format."""

import struct
import unittest

import can

from udp.message import (
	BODY_STRUCT, HEADER_SIZE, PACKET_SIZE, BridgeAction,
	can_to_udp, make_header, udp_to_can,
)


class UdpMessageTests(unittest.TestCase):
	def test_round_trip_preserves_actual_payload_for_every_classic_dlc(self):
		for dlc in range(9):
			with self.subTest(dlc=dlc):
				payload = bytes(range(dlc))
				original = can.Message(arbitration_id=0x100AAD0B,
					is_extended_id=True, data=payload)
				packet = can_to_udp(original)
				self.assertEqual(len(packet), PACKET_SIZE)
				decoded, = udp_to_can(packet)
				self.assertEqual(decoded.arbitration_id, original.arbitration_id)
				self.assertTrue(decoded.is_extended_id)
				self.assertFalse(decoded.is_remote_frame)
				self.assertEqual(decoded.dlc, dlc)
				self.assertEqual(bytes(decoded.data), payload)

	def test_short_payload_ignores_nonzero_padding(self):
		packet = make_header(BridgeAction['SEND_CAN']) + struct.pack(
			BODY_STRUCT, 0x100AAD0B, False, True, 2,
			b'\x12\x0b\xaa\xbb\xcc\xdd\xee\xff', 0)
		decoded, = udp_to_can(packet)
		self.assertEqual(decoded.dlc, 2)
		self.assertEqual(bytes(decoded.data), b'\x12\x0b')
		# Re-encoding must not reintroduce the discarded transport padding as data.
		body = struct.unpack(BODY_STRUCT, can_to_udp(decoded)[HEADER_SIZE:])
		self.assertEqual(body[3], 2)
		self.assertEqual(body[4], b'\x12\x0b' + b'\x00' * 6)

	def test_mixed_length_frames_in_one_datagram_stay_separate(self):
		lengths = (0, 2, 3, 5, 6, 8)
		originals = [can.Message(arbitration_id=0x100 + index, is_extended_id=False,
			data=bytes([index + 1]) * dlc) for index, dlc in enumerate(lengths)]
		packet = b''.join(can_to_udp(message) for message in originals)
		decoded = udp_to_can(packet)
		self.assertEqual(len(decoded), len(originals))
		for original, result in zip(originals, decoded):
			self.assertEqual(result.arbitration_id, original.arbitration_id)
			self.assertFalse(result.is_extended_id)
			self.assertEqual(result.dlc, original.dlc)
			self.assertEqual(bytes(result.data), bytes(original.data))

	def test_remote_frame_retains_requested_dlc_without_payload(self):
		original = can.Message(arbitration_id=0x123, is_extended_id=False,
			is_remote_frame=True, dlc=4)
		decoded, = udp_to_can(can_to_udp(original))
		self.assertTrue(decoded.is_remote_frame)
		self.assertEqual(decoded.dlc, 4)
		self.assertEqual(bytes(decoded.data), b'')

	def test_invalid_classic_dlc_is_skipped_without_losing_next_packet(self):
		valid = can_to_udp(can.Message(arbitration_id=0x123, data=b'\x12\x0b'))
		for dlc in (9, 255):
			with self.subTest(dlc=dlc):
				invalid = make_header(BridgeAction['SEND_CAN']) + struct.pack(
					BODY_STRUCT, 0x456, False, True, dlc, b'\xff' * 8, 0)
				self.assertEqual(udp_to_can(invalid), [])
				decoded, = udp_to_can(invalid + valid)
				self.assertEqual(decoded.arbitration_id, 0x123)
				self.assertEqual(bytes(decoded.data), b'\x12\x0b')