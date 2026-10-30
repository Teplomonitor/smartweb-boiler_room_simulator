"""Resolve GS-USB profiles by device identity rather than enumeration order."""

from pathlib import Path
import time

from can.util import load_config


CAN_CONFIG = Path(__file__).resolve().parents[1] / 'can.ini'
SCAN_ATTEMPTS = 6
SCAN_RETRY_DELAY = 0.5


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
