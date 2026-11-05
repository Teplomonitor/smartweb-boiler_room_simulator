from scenario.base.double_pump import DoublePumpScenario


class Scenario(DoublePumpScenario):
	ESTIMATED_RUN_SECONDS = 150
	FAULT_HOLD_DURATION = 10

	def get_scenario_title(self):
		return 'Сдвоенный насос: неисправность обоих насосов'

	def get_scenario_description(self):
		return 'При активном управляющем сигнале аварии обоих насосов выключают оба выхода и включают общую аварию'

	def get_checklist_id(self):
		return '3.8.3'

	def run(self):
		self.run_pump_test(self._check_both_faults)

	def _check_both_faults(self):
		self._set_input('control', 'short')
		if not self.check_state(self.one_pump_is_on, 'Рабочий насос включён до подачи аварий'):
			return False
		self._set_input('pump_1_error', 'short')
		self._set_input('pump_2_error', 'short')
		if not self.check_state(self.both_pumps_failed_and_off, 'Оба насоса неисправны и выключены, общая авария активна'):
			return False
		return self.wait_state_permanence(
			self.both_pumps_failed_and_off, self.FAULT_HOLD_DURATION,
		)