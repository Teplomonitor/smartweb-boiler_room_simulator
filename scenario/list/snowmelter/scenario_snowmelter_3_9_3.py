'''
@author: admin
'''

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error
from scenario.base.snowmelter import SnowmelterScenario   as Parent
from scenario.steps import ScenarioSteps, preserved_inputs
from math import isfinite

class Scenario(Parent):
	SWITCH_OFF_DELAY = 5 * 60
	EARLY_TOLERANCE = 5  # Polling, CAN delivery and the 2-second firmware control period.
	LATE_TOLERANCE = 10
	DELIVERY_TIMEOUT = 30
	PUMP_TIMEOUT = 60
	OFF_HOLD_DURATION = 5 * 60
	ON_HOLD_DURATION = 5
	TEMPERATURE_MARGIN = 5
	PLATE_MARGIN = 2
	TEMPERATURE_TOLERANCE = 0.2

	def get_default_preset(self):
		return 'snowmelter_virtual_outdoor'

	def force_preset_load(self):
		return True

	def get_scenario_title(self):
		return 'scenario 3'

	def get_scenario_description(self):
		return 'проверить, что снеготайка не работает, если уличная температура выше или ниже заданного диапазона (задержка 5 минут)'

	def get_checklist_id(self):
		return '3.9.3'

	def outdoorTemperatureIsHot(self, maxValue):
		oat = self.readSnowmelterOutdoorTemperature()
		return oat is not None and oat > maxValue

	def outdoorTemperatureIsCold(self, minValue):
		oat = self.readSnowmelterOutdoorTemperature()
		return oat is not None and oat < minValue

	def setHighOutdoorTemperature(self):
		maxTemp = self.readMaxOutdoorTemperature()
		self.setOutdoorTemperature(maxTemp + 5)
		return self.wait_event(self.outdoorTemperatureIsHot, 5*60, maxTemp)

	def setLowOutdoorTemperature(self):
		minTemp = self.readMinOutdoorTemperature()
		self.setOutdoorTemperature(minTemp - 5)
		return self.wait_event(self.outdoorTemperatureIsCold, 5*60, minTemp)

	def run(self):
		self._status = 'FAIL'
		try:
			self._run_temperature_cases()
		except (RuntimeError, ValueError) as error:
			print_error(str(error))

	def _send_temperature(self, temperature):
		self.setOutdoorTemperature(temperature)
		self._outdoor.publish_temperature(force=True)

	def _temperature_received(self, expected):
		value = self.readSnowmelterOutdoorTemperature()
		return isinstance(value, (int, float)) and isfinite(value) and abs(value - expected) <= self.TEMPERATURE_TOLERANCE

	def _pump_value(self, channel):
		value = channel.get_value()
		if not channel.is_mapped() or not isinstance(value, (int, float)) or not isfinite(value) or not 0 <= value <= self.RELAY_ON:
			raise RuntimeError('Не получено корректное состояние привязанного выхода насоса')
		return value

	def _pumps_off(self):
		return all(self._pump_value(channel) == self.RELAY_OFF for channel in self._pump_channels)

	def _run_temperature_cases(self):
		if self._outdoor is None or not self._outdoor.get_preset().is_virtual():
			raise RuntimeError('Для пилотного сценария нужна виртуальная улица')
		minimum = self.readMinOutdoorTemperature()
		maximum = self.readMaxOutdoorTemperature()
		plate = self.readRequiredPlateTemperatureValue()
		protection = self.readFrostProtectionTemperatureValue()
		if any(not isinstance(value, (int, float)) or not isfinite(value) for value in (minimum, maximum, plate, protection)) or minimum >= maximum:
			raise RuntimeError('Не прочитаны корректные параметры снеготайки')
		circulation = self._snowmelter.getSecondaryPumpState()
		loading = [channel for channel in (self._snowmelter.getPrimaryPumpState(),
			self._snowmelter.getAnalogPumpSignal()) if channel.is_mapped()]
		if not circulation.is_mapped() or not loading:
			raise RuntimeError('Не привязаны выходы насосов снеготайки')
		self._pump_channels = [circulation, *loading]
		sensors = [self._outdoor.getOutdoorTemperature(), self._snowmelter.getPlateTemperature(),
			self._snowmelter.getBackwardFlowTemperature()]
		if any(not sensor.is_mapped() for sensor in sensors):
			raise RuntimeError('Не привязаны обязательные входы снеготайки')
		steps = ScenarioSteps(self)
		with preserved_inputs(self, sensors):
			self.setPlateTemperature(plate - self.PLATE_MARGIN)
			# Isolate the outdoor blocking timer from independent frost protection.
			self.setBacwardFlowTemperature(protection + self.TEMPERATURE_MARGIN)
			for title, temperature in (('Жарко', maximum + self.TEMPERATURE_MARGIN),
				('Холодно', minimum - self.TEMPERATURE_MARGIN)):
				normal = (minimum + maximum) / 2
				self._send_temperature(normal)
				steps.expect('Снеготайка получила нормальную температуру',
					lambda: self._temperature_received(normal), self.DELIVERY_TIMEOUT)
				steps.expect('Циркуляционный насос включён',
					lambda: self._pump_value(circulation) != self.RELAY_OFF,
					self.PUMP_TIMEOUT, hold=self.ON_HOLD_DURATION)
				steps.delayed_change(title, lambda: self._send_temperature(temperature),
					before=lambda: self._pump_value(circulation) != self.RELAY_OFF,
					after=lambda: self._pump_value(circulation) == self.RELAY_OFF,
					received=lambda: self._temperature_received(temperature),
					delay=self.SWITCH_OFF_DELAY, delivery_timeout=self.DELIVERY_TIMEOUT,
					early_tolerance=self.EARLY_TOLERANCE, late_tolerance=self.LATE_TOLERANCE)
				steps.expect('Все используемые выходы насосов выключены', self._pumps_off,
					self.PUMP_TIMEOUT, hold=self.OFF_HOLD_DURATION)
			self._status = 'OK'
		print_log('Обе границы температуры и задержка отключения проверены')