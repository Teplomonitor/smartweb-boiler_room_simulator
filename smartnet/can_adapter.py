"""Resolve GS-USB profiles by device identity rather than enumeration order."""

from pathlib import Path
from collections import deque
import struct
import time

from can.util import load_config
from consoleLog import print_error


CAN_CONFIG = Path(__file__).resolve().parents[1] / 'can.ini'
SCAN_ATTEMPTS = 6
SCAN_RETRY_DELAY = 0.5
RECEIVE_ERROR_LIMIT = 5
RECEIVE_ERROR_WINDOW = 10.0
FAILED_RECEIVE_POLL_DELAY = 0.1


def _short_frame_details(exc):
	"""Identify a length mismatch in gs_usb's frame unpacker, not other errors."""
	traceback = exc.__traceback__
	while traceback:
		frame = traceback.tb_frame
		if (frame.f_globals.get('__name__') == 'gs_usb.gs_usb_frame'
				and frame.f_code.co_name == 'unpack_into'):
			data = frame.f_locals.get('data')
			if data is None or 'hw_timestamp' not in frame.f_locals:
				return None
			expected = 24 if frame.f_locals['hw_timestamp'] else 20
			actual = len(data)
			if actual != expected:
				return actual, expected
			return None
		traceback = traceback.tb_next
	return None


def protect_gs_usb_receive(bus, profile, on_failure):
	"""Discard occasional malformed USB frames; stop the session on a burst."""
	device = bus.gs_usb
	read = device.read
	errors = deque()
	failed = False

	def guarded_read(frame, timeout_ms):
		nonlocal failed
		if failed:
			# The owner stops the notifier asynchronously; avoid a busy loop meanwhile.
			time.sleep(min(max(timeout_ms / 1000, 0.001), FAILED_RECEIVE_POLL_DELAY))
			return False
		try:
			return read(frame=frame, timeout_ms=timeout_ms)
		except struct.error as exc:
			details = _short_frame_details(exc)
			if details is None:
				raise
			now = time.monotonic()
			while errors and now - errors[0] > RECEIVE_ERROR_WINDOW:
				errors.popleft()
			errors.append(now)
			actual, expected = details
			if len(errors) == 1:
				print_error(f'CAN {profile}: discarded malformed GS-USB frame '
					f'({actual} bytes, expected {expected})')
			if len(errors) >= RECEIVE_ERROR_LIMIT:
				failed = True
				on_failure(RuntimeError(f'CAN {profile}: {len(errors)} malformed GS-USB '
					f'frames within {RECEIVE_ERROR_WINDOW:g} seconds; '
					f'last frame {actual} bytes, expected {expected}'))
			return False

	device.read = guarded_read


def matching_indexes(devices, product, serial):
	matches = []
	for index, device in enumerate(devices):
		usb_device = device.gs_usb
		try:
			if product and usb_device.product != product:
				continue
			if serial and device.serial_number != serial:
				continue
		except (OSError, ValueError):
			continue
		matches.append(index)
	return matches


def resolve_bus_config(context, devices=None):
	"""Return python-can options for a profile; fail closed on ambiguous matches."""
	config = load_config(path=CAN_CONFIG, context=context)
	product = config.pop('product', None)
	serial = config.pop('serial', None)
	if not product and not serial:
		return config
	if config.get('interface') != 'gs_usb':
		raise ValueError(f'{context}: product/serial selectors require gs_usb')
	if devices is None:
		from can.interfaces.gs_usb import GsUsb
		for attempt in range(SCAN_ATTEMPTS):
			devices = GsUsb.scan()
			matches = matching_indexes(devices, product, serial)
			if matches or attempt == SCAN_ATTEMPTS - 1:
				break
			time.sleep(SCAN_RETRY_DELAY)
	else:
		matches = matching_indexes(devices, product, serial)
	if len(matches) != 1:
		raise ValueError(f'{context}: expected exactly one GS-USB adapter matching '
			f'product={product!r}, serial={serial!r}; found {len(matches)}')
	config.pop('bus', None)
	config.pop('address', None)
	config['index'] = matches[0]
	config['channel'] = matches[0]
	return config
