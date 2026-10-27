"""OutdoorSensorProgram::reportTemperature wire format (signed int16, little endian)."""

import math
import struct

import smartnet.constants as snc
from smartnet.message import Message
from smartnet import units


GET_TEMPERATURE = 1
REPORT_INTERVAL = 10.0


def make_temperature_message(program_id, temperature, sensor_state='normal'):
	if isinstance(program_id, bool) or not isinstance(program_id, int) or not 1 <= program_id <= 255:
		raise ValueError('Outdoor source ID must be between 1 and 255')
	if sensor_state in ('short', 'open', 'undefined'):
		raw = {'short': units.SENSOR_SHORT_VALUE, 'open': units.SENSOR_OPEN_VALUE,
			'undefined': units.SENSOR_UNDEFINED}[sensor_state]
		data = struct.pack('<H', raw)
	elif sensor_state == 'normal':
		if isinstance(temperature, bool) or not isinstance(temperature, (int, float)) or not math.isfinite(temperature):
			raise ValueError('Outdoor temperature must be a finite number')
		if not -3276.5 <= temperature <= 3276.7:
			raise ValueError('Outdoor temperature is outside the protocol range')
		data = struct.pack('<h', units.TEMPERATURE(temperature))
	else:
		raise ValueError(f'Unknown outdoor sensor state: {sensor_state}')
	return Message(snc.ProgramType.OUTDOOR_SENSOR, program_id, GET_TEMPERATURE,
		snc.RequestFlag.RESPONSE, data)