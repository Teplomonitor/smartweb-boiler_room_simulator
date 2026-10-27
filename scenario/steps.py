"""Small imperative building blocks for readable firmware scenarios.

Predicates must validate missing/invalid observations rather than treat them as
equipment states. Timing guarantees are limited by polling and transport latency.
"""

from contextlib import contextmanager
import time

from consoleLog import print_log


class ScenarioSteps:
	POLL_INTERVAL = 1

	def __init__(self, scenario, clock=None):
		self.scenario = scenario
		self.clock = clock or time.monotonic

	def _wait(self):
		if self.scenario.wait(self.POLL_INTERVAL) is False:
			raise RuntimeError('Ожидание сценария прервано')

	def expect(self, title, condition, timeout, hold=0):
		"""Reach a state, then require an uninterrupted hold (no retry on a glitch)."""
		if timeout < 0 or hold < 0:
			raise ValueError('Durations must not be negative')
		print_log(title)
		deadline = self.clock() + timeout
		while True:
			matched = condition()
			now = self.clock()
			if matched and now <= deadline:
				break
			if now >= deadline:
				raise RuntimeError(f'{title}: тайм-аут {timeout} с')
			self._wait()
		until = self.clock() + hold
		while self.clock() < until:
			self._wait()
			if not condition():
				raise RuntimeError(f'{title}: состояние нарушено во время выдержки {hold} с')

	def delayed_change(self, title, action, before, after, received,
			delay, delivery_timeout, early_tolerance, late_tolerance):
		"""Bracket receipt: earliest is action start, latest is observed delivery.

		Observe the old state even during delivery; a slow confirmation must not
		hide an early switch. The upper bound includes the receipt uncertainty.
		"""
		if min(delay, delivery_timeout, early_tolerance, late_tolerance) < 0 or early_tolerance > delay:
			raise ValueError('Invalid delayed-change timing window')
		print_log(title)
		if not before():
			raise RuntimeError(f'{title}: неверное исходное состояние')
		started = self.clock()
		action()
		delivered = None
		while True:
			was_before = before()
			if delivered is None and received():
				delivered = self.clock()
			now = self.clock()
			if delivered is not None and delivered - started > delivery_timeout:
				raise RuntimeError(f'{title}: воздействие получено слишком поздно')
			if after():
				elapsed = now - started
				if elapsed < delay - early_tolerance:
					raise RuntimeError(f'{title}: преждевременное переключение через {elapsed:.1f} с')
				if delivered is None:
					raise RuntimeError(f'{title}: получение воздействия не подтверждено')
				if now > delivered + delay + late_tolerance:
					raise RuntimeError(f'{title}: запоздалое переключение')
				print_log(f'{title}: переключение через {elapsed:.1f} с от отправки')
				return
			if not was_before:
				raise RuntimeError(f'{title}: неизвестное состояние оборудования')
			if delivered is None and now - started >= delivery_timeout:
				raise RuntimeError(f'{title}: воздействие не получено за {delivery_timeout} с')
			if delivered is not None and now >= delivered + delay + late_tolerance:
				raise RuntimeError(f'{title}: оборудование не переключилось вовремя')
			self._wait()


@contextmanager
def preserved_inputs(scenario, sensors):
	"""Restore values, fault states and original manual modes, including cancellation."""
	saved = [(sensor, sensor.get_value(), sensor.isManual(), sensor.isShort(), sensor.isOpen(),
		sensor in scenario._manualSensorsList) for sensor in sensors]
	try:
		yield
	finally:
		errors = []
		for sensor, value, manual, short, opened, tracked in reversed(saved):
			try:
				try:
					sensor.set_manual(True)
					sensor.set_value(value, True)
					if short or opened:
						sensor.set_value('short' if short else 'open', True)
				finally:
					sensor.set_manual(manual)
			except Exception as error:
				errors.append(str(error))
			finally:
				if not tracked and sensor in scenario._manualSensorsList:
					scenario._manualSensorsList.remove(sensor)
		if errors:
			scenario._status = 'FAIL'
			raise RuntimeError('Не восстановлены входы: ' + '; '.join(errors))