"""Web mapping tests with automatic preparation of the selected CAN target."""

import time

import main
import mainThread
import smartnet.constants as snc
from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent, ThreadStoppedException
from smartnet.mapping_client import (
	MappingCanClient, UNDEFINED_MAPPING, SENSOR_LOCAL, RELAY_LOCAL,
	PROGRAM_OUTPUT, is_undefined, mappings_equal, pack_mapping,
)


class WebBindingScenario(Parent):
	PROGRAM_ID = 101
	INPUT_COUNT = 4
	OUTPUT_COUNT = 5
	REQUIRED_INPUT_COUNT = 0
	REQUIRED_RELAY_COUNT = 0
	APPLY_TIMEOUT = 15
	POLL_INTERVAL = 1

	def get_required_programs(self):
		return {'test_program': snc.ProgramType.DOUBLE_PUMP}

	def get_default_preset(self):
		return 'web_bindings'

	def force_preset_load(self):
		# Each run needs a clean controller, even after another web scenario.
		return True

	def init_scenario(self):
		self._programList = {}
		worker = mainThread.MainThread()
		self._web = worker.web_client
		if self._web is None:
			raise RuntimeError('Web scenario requires --web-url and explicit --id')
		self._controller_id = self._controllerHost.get_controller_id()
		if not 1 <= self._controller_id <= 255 or worker._debug:
			raise RuntimeError('Web tests require a real, explicitly addressed CAN target')
		# Let any startup preset finish before checking and resetting the target.
		while not main.loadPresetDone():
			self.wait(self.POLL_INTERVAL)
		self._can = MappingCanClient()
		self._channel_counts = self._can.read_channel_counts(self._controller_id)
		input_count, relay_count = self._channel_counts
		print_log(f'CAN target {self._controller_id}: inputs={input_count}, relays={relay_count}')
		if any(type(count) is not int or not 0 <= count <= 32 for count in self._channel_counts):
			raise RuntimeError(f'Unsupported CAN channel counts: {self._channel_counts}')
		if input_count < self.REQUIRED_INPUT_COUNT or relay_count < self.REQUIRED_RELAY_COUNT:
			raise RuntimeError(f'CAN target {self._controller_id}: requires at least '
				f'{self.REQUIRED_INPUT_COUNT} inputs and {self.REQUIRED_RELAY_COUNT} relays; '
				f'got {input_count} inputs and {relay_count} relays')
		# The HTTP endpoint is a gateway; it need not belong to the CAN target.
		try:
			self._web.login()
			self._check_web_target(require_program=False)
		finally:
			self._web.logout()
		super().init_scenario()
		if self._programList['test_program'].get_id() != self.PROGRAM_ID:
			raise RuntimeError('Unexpected web test program ID')

	def _check_web_target(self, require_program=True):
		config = self._web.config()
		controllers = [item for item in config['controllers']
			if item.get('id') == self._controller_id]
		if len(controllers) != 1:
			raise RuntimeError('HTTP server does not expose the selected CAN controller ID')
		for controller in config['controllers']:
			if controller.get('id') != self._controller_id and any(
					program.get('id') == self.PROGRAM_ID for program in controller.get('programs', [])):
				raise RuntimeError(f'Test program ID {self.PROGRAM_ID} is already used by '
					f'CAN controller {controller.get("id")}')
		if not require_program:
			return
		programs = controllers[0].get('programs', [])
		matches = [program for program in programs if program.get('id') == self.PROGRAM_ID]
		if len(matches) != 1 or matches[0].get('type') != int(snc.ProgramType.DOUBLE_PUMP):
			raise RuntimeError('HTTP configuration must expose the web test double-pump program on the selected controller')

	def _read(self, key):
		kind, index = key
		host_id = self._controller_id if kind == 'relay' else self.PROGRAM_ID
		return getattr(self._can, f'read_{kind}')(host_id, index)

	def _snapshot(self):
		return {(kind, index): self._read((kind, index))
			for kind, count in (('input', self.INPUT_COUNT), ('output', self.OUTPUT_COUNT),
				('relay', self._channel_counts[1])) for index in range(count)}

	def _check_initial_state(self, saved):
		# Avoid altering other programs through forward/reverse mapping propagation.
		if any(not is_undefined(saved['output', i]) for i in range(self.OUTPUT_COUNT)):
			raise RuntimeError('Test program outputs must initially be unbound')
		if self.REQUIRED_RELAY_COUNT and not is_undefined(saved['relay', 0]):
			raise RuntimeError('Test relay 0 must initially be unbound')
		if any(raw >> 13 not in (0, 2, 7) for (kind, _), raw in saved.items() if kind == 'input'):
			raise RuntimeError('Test inputs must not be bound to other programs')
		if any(raw >> 13 in (5, 6) and raw & 255 == self.PROGRAM_ID
				for (kind, _), raw in saved.items() if kind == 'relay'):
			raise RuntimeError('A relay is already bound to a test program output')

	def _differences(self, expected, actual):
		return [f'{kind}[{index}]: expected=0x{value:04X}, CAN=0x{actual[kind, index]:04X}'
			for (kind, index), value in expected.items()
			if not mappings_equal(value, actual[kind, index])]

	def _command_and_check(self, description, command, changes):
		if self.is_stopped():
			raise ThreadStoppedException('Web binding test cancelled')
		print_log(description)
		expected = dict(self._saved)
		expected.update(changes)
		try:
			response = command()
			print_log(f'HTTP: partial={response.get("partial")}, error=none')
		except Exception:
			# Report actual CAN state but never retry an uncertain web mutation.
			try:
				actual = self._snapshot()
				print_error('HTTP failed; CAN readback: ' + ('; '.join(self._differences(expected, actual))
					or 'requested mapping is present (HTTP step still failed)'))
			except Exception as error:
				print_error(f'CAN readback after HTTP failure failed: {error}')
			raise
		deadline = time.monotonic() + self.APPLY_TIMEOUT
		while True:
			actual = self._snapshot()
			differences = self._differences(expected, actual)
			if not differences:
				print_log('CAN: requested bindings confirmed; other bindings unchanged')
				return
			if time.monotonic() >= deadline:
				raise RuntimeError('; '.join(differences))
			self.wait(self.POLL_INTERVAL)

	def run_binding_test(self, sequence):
		self._status = 'FAIL'
		try:
			self._web.login()
			self._check_web_target()
			self._saved = self._snapshot()
			self._check_initial_state(self._saved)
			sequence()
			self._status = 'OK'
		except ThreadStoppedException:
			self._status = 'FAIL'
			raise
		except Exception as error:
			self._status = 'FAIL'
			print_error(f'Web binding test failed: {error}')
		finally:
			try:
				self._web.logout()
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Web logout failed: {error}')

	def check_input_sequence(self):
		key = ('input', 0)
		for sensor_id in (0, 0, 1):
			self._command_and_check(f'Bind input 0 to local sensor {sensor_id}',
				lambda: self._web.bind_input(self.PROGRAM_ID, 0, self._controller_id, sensor_id),
				{key: pack_mapping(self._controller_id, sensor_id, SENSOR_LOCAL)})
		for _ in range(2):
			self._command_and_check('Unbind input 0',
				lambda: self._web.unbind_input(self.PROGRAM_ID, 0), {key: UNDEFINED_MAPPING})

	def check_relay_sequence(self):
		for output_id in (0, 0, 1):
			changes = {('relay', 0): pack_mapping(self.PROGRAM_ID, output_id, PROGRAM_OUTPUT),
				('output', output_id): pack_mapping(self._controller_id, 0, RELAY_LOCAL),
				('output', 1 - output_id): UNDEFINED_MAPPING}
			self._command_and_check(f'Bind relay 0 to program output {output_id}',
				lambda: self._web.bind_relay(self._controller_id, 0, self.PROGRAM_ID, output_id), changes)
		for _ in range(2):
			self._command_and_check('Unbind relay 0',
				lambda: self._web.unbind_relay(self._controller_id, 0),
				{('relay', 0): UNDEFINED_MAPPING, ('output', 0): UNDEFINED_MAPPING,
					('output', 1): UNDEFINED_MAPPING})