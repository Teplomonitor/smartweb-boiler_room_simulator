"""List adapters visible through python-can's GS-USB backend.

This utility only enumerates devices; it does not open the CAN bus, change
bit timing, or transmit frames.
"""

from __future__ import annotations

import sys


def main() -> int:
	try:
		from can.interfaces.gs_usb import GsUsb
	except ImportError as exc:
		print(f'GS-USB support is unavailable: {exc}', file=sys.stderr)
		print('Install project dependencies, including PyUSB.', file=sys.stderr)
		return 1

	try:
		devices = GsUsb.scan()
	except Exception as exc:
		print(f'Unable to enumerate GS-USB devices: {exc}', file=sys.stderr)
		print('Check the Windows USB driver and adapter connection.', file=sys.stderr)
		return 1

	if not devices:
		print('No GS-USB devices found.')
		return 0

	print(f'Found {len(devices)} GS-USB device(s):')
	for index, device in enumerate(devices):
		bus = getattr(device, 'bus', '?')
		address = getattr(device, 'address', '?')
		usb_device = getattr(device, 'gs_usb', None)
		ports = getattr(usb_device, 'port_numbers', None)
		try:
			product = getattr(usb_device, 'product', None)
		except Exception:
			product = None
		print(f'  index={index}: bus={bus}, address={address}, '
			f'ports={ports}, product={product or "?"}')

	print('Use the displayed index in can.ini (for example, index = 0).')
	return 0


if __name__ == '__main__':
	raise SystemExit(main())