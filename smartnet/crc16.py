"""Shared CRC16-CCITT implementation used by SmartNet protocols."""


class CRC16:
	"""CRC16 CCITT implementation matching the controller's ``crc16.c``."""

	_CRC16_LOOKUP_HIGH = (
		0x00, 0x10, 0x20, 0x30, 0x40, 0x50, 0x60, 0x70,
		0x81, 0x91, 0xA1, 0xB1, 0xC1, 0xD1, 0xE1, 0xF1,
	)
	_CRC16_LOOKUP_LOW = (
		0x00, 0x21, 0x42, 0x63, 0x84, 0xA5, 0xC6, 0xE7,
		0x08, 0x29, 0x4A, 0x6B, 0x8C, 0xAD, 0xCE, 0xEF,
	)

	def __init__(self):
		self.high = 0xFF
		self.low = 0xFF

	def add_byte(self, value):
		"""Add one byte to the CRC, processing high and low nibbles."""
		self._update_4bits(value >> 4)
		self._update_4bits(value & 0x0F)

	def _update_4bits(self, value):
		lookup_index = (self.high >> 4) ^ value
		self.high = ((self.high << 4) | (self.low >> 4)) & 0xFF
		self.low = (self.low << 4) & 0xFF
		self.high ^= self._CRC16_LOOKUP_HIGH[lookup_index]
		self.low ^= self._CRC16_LOOKUP_LOW[lookup_index]

	def get(self):
		"""Return the current CRC as a 16-bit integer."""
		return ((self.high << 8) | self.low) & 0xFFFF

	@staticmethod
	def calc(data):
		"""Calculate CRC16 for an iterable of byte values."""
		crc = CRC16()
		for value in data:
			crc.add_byte(value)
		return crc.get()
