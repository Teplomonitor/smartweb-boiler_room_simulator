"""TemperatureSourceProgram::sendCoolingRequest wire format."""

import smartnet.constants as snc
from smartnet.message import CanBusInterface, Message


SET_COOLING = 3  # heat::ConsumerProgram::SET_COOLING
COOLING_OFF = 0
COOLING_ON = 1
BROADCAST_ID = 0


def make_cooling_request(source_id, enabled):
	if isinstance(source_id, bool) or not isinstance(source_id, int) or not 1 <= source_id <= 255:
		raise ValueError('Cooling source ID must be between 1 and 255')
	return Message(snc.ProgramType.CONSUMER, BROADCAST_ID, SET_COOLING,
		snc.RequestFlag.REQUEST, bytes((source_id, COOLING_ON if enabled else COOLING_OFF)))


def send_cooling_request(source_id, enabled):
	"""Propagate send errors: a failed request must not count as a successful test."""
	CanBusInterface().get().send(make_cooling_request(source_id, enabled).smartNetToCanMsg(), timeout=1.0)