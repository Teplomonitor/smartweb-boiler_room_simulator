from consoleLog import print_error, print_log
from scenario.base.double_pump import DoublePumpScenario
from scenario.base.journal import JournalScenarioMixin
from smartnet.message_log_constants import MessageLogCode, SeverityCode


class Scenario(JournalScenarioMixin, DoublePumpScenario):
	ESTIMATED_RUN_SECONDS = 150
	FAULT_INPUT_DURATION = 5
	FLOW_FAILURE_DELAY = 30
	FLOW_TIMEOUT_MARGIN = 15
	JOURNAL_TIMEOUT = 30

	def get_scenario_title(self):
		return 'Journal: double pump failure'

	def get_scenario_description(self):
		return ('Авария «неисправен насос» записывается в журнал при замыкании '
			'каждого входа неисправности на 5 секунд и при отсутствии протока '
			'после 30 секунд работы насоса')

	def get_checklist_id(self):
		return '9.27'

	def force_preset_load(self):
		return True

	def run(self):
		self.run_pump_test(self._check_journal_faults)

	def _pump_has_fault(self, index):
		return (
			self._pump.read_parameter_value(f'pump_{index}_status') == self.PUMP_FAULT
			and self._alarm_is(True)
		)

	def _wait_fault_entry(self):
		return self.wait_journal_entry(
			MessageLogCode.MLC_DOUBLE_PUMP_FAILURE,
			SeverityCode.SC_CRITICAL,
			self._pump.get_id(),
			self.JOURNAL_TIMEOUT,
		)

	def _reset_between_checks(self):
		self._clear_test_faults()
		return self.check_state(self._healthy_and_off, 'Авария сброшена, оба насоса выключены')

	def _check_fault_input(self, index):
		print_log(f'Проверка журнала: вход «Неисправность {index}»')
		self._set_input('control', 'short')
		if not self.check_state(self.one_pump_is_on, 'Один насос работает с нормальным протоком'):
			return False
		if not self.snapshot_journal():
			return False
		self._set_input(f'pump_{index}_error', 'short')
		self.wait(self.FAULT_INPUT_DURATION)
		if not self.check_state(lambda: self._pump_has_fault(index), f'Насос {index} неисправен'):
			return False
		return self._wait_fault_entry()

	def _check_missing_flow(self):
		print_log('Проверка журнала: работа насоса без протока в течение 30 секунд')
		if not self.snapshot_journal():
			return False
		# Override automatic flow before starting, so the 30-second check sees no flow.
		self._set_input('flow', 'open')
		self._set_input('control', 'short')
		if not self.check_state(self.one_pump_is_on, 'Один насос включён без протока'):
			return False
		states = self._pump_states()
		if states is None or sum(states) != 1:
			print_error('Не удалось определить работающий насос')
			return False
		index = states.index(True) + 1
		if not self.wait_event(
			lambda: self._pump_has_fault(index),
			self.FLOW_FAILURE_DELAY + self.FLOW_TIMEOUT_MARGIN,
		):
			print_error('Работающий насос без протока не признан неисправным')
			return False
		# Prevent the reserve pump from failing while the journal is being read.
		self._pump.get_input_channel('flow').set_manual(False)
		return self._wait_fault_entry()

	def _check_journal_faults(self):
		for index in (1, 2):
			if not self._check_fault_input(index) or not self._reset_between_checks():
				return False
		return self._check_missing_flow()