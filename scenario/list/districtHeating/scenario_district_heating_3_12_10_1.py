from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 420
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ALARM_RESPONSE_TIMEOUT = 3 * 60
	ALARM_RESPONSE_STABILIZATION_DURATION = 30

	def get_scenario_title(self):
		return 'District Heating: reserve generator work is enabled by an alarm signal'

	def get_scenario_description(self):
		return (
			'Резервный генератор: разрешена работа, если ИТП получил сигнал аварии '
			'от аварийной программы'
		)

	def get_checklist_id(self):
		return '3.12.10.1'

	def get_default_preset(self):
		return 'district_heating_3_12_10'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'boiler': snc.ProgramType.BOILER,
			'circuit': snc.ProgramType.HEATING_CIRCUIT,
			'alarm': snc.ProgramType.FILLING_LOOP,
		}

	def run(self):
		self.run_pressure_alarm_check(reserve=True)