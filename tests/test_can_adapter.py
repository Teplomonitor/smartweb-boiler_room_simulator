"""GS-USB identity resolution without a USB device or CAN traffic."""

from types import SimpleNamespace
import unittest
from unittest.mock import patch

from smartnet.can_adapter import resolve_bus_config


def device(product, serial):
	return SimpleNamespace(gs_usb=SimpleNamespace(product=product), serial_number=serial)


class TestCanAdapter(unittest.TestCase):
	def test_named_profiles_follow_devices_after_reordering(self):
		devices = [device('candleLight USB to CAN adapter', 'light'),
			device('UCAN USB to CAN adapter', 'ucan')]
		self.assertEqual(resolve_bus_config('ucan', devices)['index'], 1)
		self.assertEqual(resolve_bus_config('candleLightGsUsb', devices)['index'], 0)
		self.assertEqual(resolve_bus_config('ucan', devices)['channel'], 1)
		self.assertNotIn('product', resolve_bus_config('ucan', devices))

	def test_missing_or_duplicate_identity_fails_closed(self):
		for devices in ([], [device('UCAN USB to CAN adapter', 'a'),
				device('UCAN USB to CAN adapter', 'b')]):
			with self.subTest(devices=devices), self.assertRaisesRegex(ValueError,
					'exactly one'):
				resolve_bus_config('ucan', devices)

	def test_serial_selector_disambiguates_identical_products(self):
		devices = [device('same', 'first'), device('same', 'second')]
		with patch('smartnet.can_adapter.load_config', return_value={
			'interface': 'gs_usb', 'product': 'same', 'serial': 'second',
			'bitrate': 20000, 'channel': None}):
			self.assertEqual(resolve_bus_config('same', devices)['index'], 1)

	def test_legacy_numbered_profile_does_not_scan(self):
		with patch('can.interfaces.gs_usb.GsUsb.scan', side_effect=AssertionError('scanned')):
			self.assertEqual(resolve_bus_config('canable0')['index'], 0)

	def test_transient_empty_scan_recovers_without_using_wrong_adapter(self):
		devices = [device('UCAN USB to CAN adapter', 'ucan'),
			device('candleLight USB to CAN adapter', 'light')]
		with patch('can.interfaces.gs_usb.GsUsb.scan', side_effect=[devices[:1], devices]) as scan, \
				patch('smartnet.can_adapter.time.sleep') as sleep:
			self.assertEqual(resolve_bus_config('candleLightGsUsb')['index'], 1)
		self.assertEqual(scan.call_count, 2)
		sleep.assert_called_once()

	def test_permanently_missing_adapter_stops_after_bounded_attempts(self):
		with patch('can.interfaces.gs_usb.GsUsb.scan', return_value=[]) as scan, \
				patch('smartnet.can_adapter.time.sleep'):
			with self.assertRaisesRegex(ValueError, 'found 0'):
				resolve_bus_config('candleLightGsUsb')
		self.assertEqual(scan.call_count, 6)

	def test_descriptor_error_is_reported(self):
		class BrokenUsb:
			@property
			def product(self):
				raise OSError('device busy')
		with self.assertRaisesRegex(ValueError, 'among 1 device.*device busy'):
			resolve_bus_config('ucan', [SimpleNamespace(gs_usb=BrokenUsb())])
		with self.assertRaisesRegex(ValueError, 'found 1.*device busy'):
			resolve_bus_config('ucan', [device('UCAN USB to CAN adapter', 'ucan'),
				SimpleNamespace(gs_usb=BrokenUsb())])

	def test_assigned_location_checks_only_target_and_uses_bus_address(self):
		adapter = device('UCAN USB to CAN adapter', 'ucan')
		location = {'context': 'ucan', 'bus': 2, 'address': 3}
		with patch('can.interfaces.gs_usb.GsUsb.find', return_value=adapter) as find, \
				patch('can.interfaces.gs_usb.GsUsb.scan', side_effect=AssertionError('scanned')), \
				patch('usb.util.dispose_resources') as dispose:
			config = resolve_bus_config('ucan', location=location)
		find.assert_called_once_with(bus=2, address=3)
		dispose.assert_called_once_with(adapter.gs_usb)
		self.assertEqual((config['bus'], config['address']), (2, 3))
		self.assertNotIn('index', config)
		self.assertNotIn('product', config)

	def test_assigned_location_rejects_mismatch_and_releases_handle(self):
		adapter = device('wrong device', 'other')
		location = {'context': 'ucan', 'bus': 2, 'address': 3}
		with patch('can.interfaces.gs_usb.GsUsb.find', return_value=adapter), \
				patch('usb.util.dispose_resources') as dispose:
			with self.assertRaisesRegex(ValueError, 'does not match'):
				resolve_bus_config('ucan', location=location)
		dispose.assert_called_once_with(adapter.gs_usb)
		with patch('can.interfaces.gs_usb.GsUsb.find', return_value=None):
			with self.assertRaisesRegex(ValueError, 'unavailable'):
				resolve_bus_config('ucan', location=location)
		for bad in ({'context': 'other', 'bus': 2, 'address': 3},
				{'context': 'ucan', 'bus': True, 'address': 3}, {}):
			with self.subTest(location=bad), self.assertRaisesRegex(ValueError, 'invalid'):
				resolve_bus_config('ucan', location=bad)
		with self.assertRaisesRegex(ValueError, 'requires product/serial'):
			resolve_bus_config('canable0', location=location)

	def test_application_bus_uses_assigned_location(self):
		from smartnet.message import createBus
		location = '{"context":"ucan","bus":2,"address":3}'
		with patch.dict('os.environ', {'BRS_GS_USB_LOCATION': location}), \
				patch('smartnet.message.resolve_bus_config', return_value={'interface': 'virtual'}) as resolve, \
				patch('smartnet.message.can.Bus'):
			createBus('ucan')
		resolve.assert_called_once_with('ucan', location={'context': 'ucan', 'bus': 2, 'address': 3})
		for bad in ('null', '[]', 'not json'):
			with self.subTest(location=bad), patch.dict('os.environ', {'BRS_GS_USB_LOCATION': bad}), \
					self.assertRaisesRegex(ValueError, 'invalid assigned'):
				createBus('ucan')

	def test_application_bus_uses_resolved_index(self):
		from smartnet.message import createBus
		devices = [device('candleLight USB to CAN adapter', 'light'),
			device('UCAN USB to CAN adapter', 'ucan')]
		with patch('can.interfaces.gs_usb.GsUsb.scan', return_value=devices), \
				patch('smartnet.message.can.Bus') as bus:
			createBus('ucan')
		self.assertEqual(bus.call_args.kwargs['index'], 1)
		self.assertNotIn('product', bus.call_args.kwargs)


if __name__ == '__main__':
	unittest.main()
