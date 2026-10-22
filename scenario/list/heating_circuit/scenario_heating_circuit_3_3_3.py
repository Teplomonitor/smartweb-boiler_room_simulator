import math

from consoleLog import print_error
from scenario.base.heating_circuit_mixer import HeatingCircuitMixerScenario
import smartnet.constants as snc


class Scenario(HeatingCircuitMixerScenario):
	def get_checklist_id(self):
		return '3.3.3'

	def get_default_preset(self):
		return 'heating_circuit_3_3_3'

	def get_scenario_title(self):
		return 'Heating circuit: three-point mixer temperature control'

	def get_scenario_description(self):
		return 'Трёхточечный смеситель: ' + super().get_scenario_description()

	def _settings(self):
		return super()._settings() + [
			# Do not let an end-position timer mask temperature regulation.
			(self._circuit, snc.ProgramType.HEATING_CIRCUIT,
			 snc.HeatingCircuitParameterId.VALVE_BLOCK, 0),
		]

	def _get_valve_channels(self):
		self._valve_open = self._circuit.get_output_channel('tptValveOpen')
		self._valve_close = self._circuit.get_output_channel('tptValveClose')
		return self._valve_open, self._valve_close

	def _valve_mappings_valid(self):
		# The model gives the analog output precedence if both are mapped.
		return not self._circuit.get_output_channel('analogValve').is_mapped()

	def _valve_position(self):
		# Reuse the physical actuator model; do not integrate travel in scenarios.
		return self._model.getValveState() * self.RELAY_MAX

	def _sample(self):
		sample = super()._sample()
		sample.update(
			valve_open=self._valve_open.get_value(),
			valve_close=self._valve_close.get_value(),
		)
		return sample

	def _sample_is_safe(self, sample):
		outputs = sample['valve_open'], sample['valve_close']
		if any(value not in (self.RELAY_OFF, self.RELAY_ON) for value in outputs):
			print_error(f'Некорректные состояния реле трёхточечного смесителя: {outputs}')
			return False
		if outputs == (self.RELAY_ON, self.RELAY_ON):
			print_error('Одновременно включены открытие и закрытие смесителя')
			return False
		return True

	def run(self):
		self._status = 'FAIL'
		circuit = self._programList['heating_circuit']
		running_time = circuit.get_parameters().get('valve_running_time')
		if running_time is None:
			print_error('Не найдено время хода смесителя в модели контура')
			return
		saved_time = running_time.get_value()
		if not isinstance(saved_time, (int, float)) or not math.isfinite(saved_time) or saved_time <= 0:
			print_error('Некорректное исходное время хода смесителя в модели')
			return
		try:
			# RemoteControl and the physical model both use seconds here.
			running_time.set_value(self.VALVE_RUNNING_TIME)
			self._run_test()
		finally:
			try:
				running_time.set_value(saved_time)
			except Exception as error:
				self._status = 'FAIL'
				print_error(f'Не восстановлено время хода смесителя в модели: {error}')
