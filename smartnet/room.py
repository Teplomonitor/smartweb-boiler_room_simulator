"""Room-device group commands matching RoomDeviceProgram::OnCANMessageReceived."""

import smartnet.constants as snc
from smartnet.message import Message


BROADCAST_ID = 0


def make_group_work_mode_message(group, mode):
	if not isinstance(group, int) or isinstance(group, bool) or not 1 <= group <= 255:
		raise ValueError('room group must be between 1 and 255')
	mode = snc.RoomWorkMode(mode)
	return Message(
		snc.ProgramType.ROOM_DEVICE, BROADCAST_ID,
		snc.RoomDeviceFunction.SET_WORK_MODE, snc.RequestFlag.REQUEST,
		[group, int(mode)],
	)


def set_group_work_mode(group, mode):
	# There is no command acknowledgement: callers must read each room's mode.
	make_group_work_mode_message(group, mode).send()
