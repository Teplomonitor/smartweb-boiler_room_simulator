"""Bounded, read-only SmartNet CAN round trip on each selected physical bus.

Only GET_ACTIVE_PROGRAMS_LIST is transmitted; no preset or I/O is modified.
"""

import argparse
from pathlib import Path
import sys
import time

import can

CAN_CONFIG = Path(__file__).resolve().parents[1] / 'can.ini'
sys.path.insert(0, str(CAN_CONFIG.parent))

import smartnet.constants as snc
from smartnet.can_adapter import resolve_bus_config


ANNOUNCEMENT_TIMEOUT = 15
RESPONSE_TIMEOUT = 5


def receive_controller_message(bus, function, controller_id, timeout):
	deadline = time.monotonic() + timeout
	while time.monotonic() < deadline:
		frame = bus.recv(min(0.5, max(0, deadline - time.monotonic())))
		if frame is None or not frame.is_extended_id or frame.is_remote_frame:
			continue
		header = frame.arbitration_id
		if ((header & 0xFF) != snc.ProgramType.CONTROLLER
				or ((header >> 16) & 0xFF) != function
				or ((header >> 24) & 0xFF) != snc.RequestFlag.RESPONSE
				or (controller_id is not None and ((header >> 8) & 0xFF) != controller_id)):
			continue
		if not frame.data:
			continue
		return frame
	return None


def check_bus(context, bus_factory=can.Bus, announcement_timeout=ANNOUNCEMENT_TIMEOUT,
		response_timeout=RESPONSE_TIMEOUT):
	config = resolve_bus_config(context)
	if config['interface'] in (None, 'virtual'):
		raise ValueError(f'{context}: select a physical CAN interface from can.ini')
	with bus_factory(**config) as bus:
		announcement = receive_controller_message(
			bus, snc.ControllerFunction.I_AM_HERE, None, announcement_timeout)
		if announcement is None:
			raise TimeoutError(f'{context}: no controller announcement received')
		controller_id = (announcement.arbitration_id >> 8) & 0xFF
		print(f'[{context}] RX announcement: controller {controller_id}', flush=True)
		request_id = (int(snc.ProgramType.CONTROLLER) | (controller_id << 8)
			| (int(snc.ControllerFunction.GET_ACTIVE_PROGRAMS_LIST) << 16)
			| (int(snc.RequestFlag.REQUEST) << 24))
		bus.send(can.Message(arbitration_id=request_id, is_extended_id=True, data=[]))
		print(f'[{context}] TX read-only program list request', flush=True)
		response = receive_controller_message(
			bus, snc.ControllerFunction.GET_ACTIVE_PROGRAMS_LIST, controller_id,
			response_timeout)
		if response is None:
			raise TimeoutError(f'{context}: no program list response from controller {controller_id}')
		programs = [(response.data[i], response.data[i + 1])
			for i in range(0, len(response.data) - 1, 2)
			if response.data[i]]
		print(f'[{context}] RX program list from {controller_id}: {programs}', flush=True)
		return controller_id, programs


def main(argv=None):
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--can', nargs='+', required=True, metavar='CONTEXT',
		help='physical CAN contexts defined in can.ini (for example ucan candleLightGsUsb)')
	parser.add_argument('--announcement-timeout', type=float, default=ANNOUNCEMENT_TIMEOUT)
	parser.add_argument('--response-timeout', type=float, default=RESPONSE_TIMEOUT)
	args = parser.parse_args(argv)
	if args.announcement_timeout <= 0 or args.response_timeout <= 0:
		parser.error('timeouts must be positive')
	failed = False
	for context in args.can:
		try:
			check_bus(context, announcement_timeout=args.announcement_timeout,
				response_timeout=args.response_timeout)
		except (can.CanError, OSError, ValueError, TimeoutError) as exc:
			failed = True
			print(f'[{context}] FAIL: {exc}', flush=True)
	return 1 if failed else 0


if __name__ == '__main__':
	raise SystemExit(main())
