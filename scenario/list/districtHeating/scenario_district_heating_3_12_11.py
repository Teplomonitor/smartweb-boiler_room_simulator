from scenario.base.district_heating_checks import DistrictHeatingChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 420
	STARTUP_TIMEOUT = 2 * 60
	STARTUP_STABILIZATION_DURATION = 20
	ALARM_RESPONSE_TIMEOUT = 3 * 60
	ALARM_RESPONSE_STABILIZATION_DURATION = 30

	def get_scenario_title(self):
		return 'District Heating: emergency signal switches off pumps and closes valve'

	def get_scenario_description(self):
		return (
			'Если ИТП получает сигнал аварии от программы подпитки при низком давлении, '
			'насосы загрузки и циркуляции выключаются, а кран закрывается'
		)

	def get_checklist_id(self):
		return '3.12.11'

	def get_default_preset(self):
		return 'district_heating_3_12_11'

	def force_preset_load(self):
		return True

	def get_required_programs(self):
		return {
			'districtHeating': snc.ProgramType.DISTRICT_HEATING,
			'outdoor': snc.ProgramType.OUTDOOR_SENSOR,
			'heatingCircuit': snc.ProgramType.HEATING_CIRCUIT,
			'alarm': snc.ProgramType.FILLING_LOOP,
		}

	def run(self):
		self.run_pressure_alarm_check()