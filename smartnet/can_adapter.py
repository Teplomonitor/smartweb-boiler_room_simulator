"""Resolve GS-USB profiles by device identity rather than enumeration order."""

from pathlib import Path
from collections import deque
from importlib.metadata import PackageNotFoundError, version
import struct
import time

from can.util import load_config
from consoleLog import print_error, print_log


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
	bus._brs_gs_usb = True
	from gs_usb.constants import GS_CAN_MODE_HW_TIMESTAMP
	flags = getattr(device, 'device_flags', None)
	timestamp = bool(flags & GS_CAN_MODE_HW_TIMESTAMP) if isinstance(flags, int) else None
	versions = {}
	for package in ('python-can', 'gs-usb', 'pyusb'):
		try:
			versions[package] = version(package)
		except PackageNotFoundError:
			versions[package] = 'unknown'
	print_log(f'CAN {profile}: GS-USB bus={getattr(device, "bus", None)} '
		f'address={getattr(device, "address", None)} '
		f'bitrate={getattr(bus, "_bitrate", None)} flags={flags!r} '
		f'hw_timestamp={timestamp} versions={versions}')
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


def matching_indexes(devices, product, serial, errors=None):
	matches = []
	for index, device in enumerate(devices):
		usb_device = device.gs_usb
		try:
			if product and usb_device.product != product:
				continue
			if serial and device.serial_number != serial:
				continue
		except (OSError, ValueError) as exc:
			if errors is not None:
				errors.append(f'index={index}: {exc!r}')
			continue
		matches.append(index)
	return matches


def resolve_bus_config(context, devices=None, location=None):
	"""Return python-can options for a profile; fail closed on ambiguous matches."""
	config = load_config(path=CAN_CONFIG, context=context)
	product = config.pop('product', None)
	serial = config.pop('serial', None)
	if not product and not serial:
		if location is not None:
			raise ValueError(f'{context}: assigned GS-USB location requires product/serial selectors')
		return config
	if config.get('interface') != 'gs_usb':
		raise ValueError(f'{context}: product/serial selectors require gs_usb')
	if location is not None:
		from can.interfaces.gs_usb import GsUsb
		from usb.util import dispose_resources
		if (not isinstance(location, dict) or location.get('context') != context
				or type(location.get('bus')) is not int or location['bus'] < 0
				or type(location.get('address')) is not int or location['address'] < 0):
			raise ValueError(f'{context}: invalid assigned GS-USB location')
		bus, address = location['bus'], location['address']
		device = GsUsb.find(bus=bus, address=address)
		if device is None:
			raise ValueError(f'{context}: assigned GS-USB adapter at bus={bus}, address={address} is unavailable')
		try:
			errors = []
			matches = matching_indexes([device], product, serial, errors)
			if not matches:
				detail = f'; descriptor errors: {", ".join(errors)}' if errors else ''
				raise ValueError(f'{context}: assigned GS-USB adapter at bus={bus}, address={address} '
					f'does not match product={product!r}, serial={serial!r}{detail}')
		finally:
			dispose_resources(device.gs_usb)
		config.pop('index', None)
		config.update(bus=bus, address=address, channel=f'{bus}:{address}')
		return config
	errors = []
	if devices is None:
		from can.interfaces.gs_usb import GsUsb
		for attempt in range(SCAN_ATTEMPTS):
			devices = GsUsb.scan()
			errors = []
			matches = matching_indexes(devices, product, serial, errors)
			if (matches and not errors) or attempt == SCAN_ATTEMPTS - 1:
				break
			time.sleep(SCAN_RETRY_DELAY)
	else:
		matches = matching_indexes(devices, product, serial, errors)
	if len(matches) != 1 or errors:
		detail = f'; descriptor errors: {", ".join(errors)}' if errors else ''
		raise ValueError(f'{context}: expected exactly one GS-USB adapter matching '
			f'product={product!r}, serial={serial!r}; found {len(matches)} '
			f'among {len(devices)} device(s){detail}')
	config.pop('bus', None)
	config.pop('address', None)
	config['index'] = matches[0]
	config['channel'] = matches[0]
	return config
