from scenario.base.double_pump import DoublePumpScenario


class Scenario(DoublePumpScenario):
	ESTIMATED_RUN_SECONDS = 180
	CONTROL_CYCLES = 2

	def get_scenario_title(self):
		return 'Сдвоенный насос: внешний управляющий сигнал'

	def get_scenario_description(self):
		return 'Два цикла: замыкание управляющего входа включает рабочий насос, размыкание выключает оба'

	def get_checklist_id(self):
		return '3.8.2'

	def run(self):
		self.run_pump_test(self._check_control_signal)

	def _check_control_signal(self):
		for cycle in range(1, self.CONTROL_CYCLES + 1):
			self._set_input('control', 'short')
			if not self.check_state(self.one_pump_is_on, f'Цикл {cycle}: рабочий насос включён'):
				return False
			self._set_input('control', 'open')
			if not self.check_state(self.pumps_are_off, f'Цикл {cycle}: оба насоса выключены'):
				return False
		return True