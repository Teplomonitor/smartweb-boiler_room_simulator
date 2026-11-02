from scenario.base.district_heating_checks import DistrictHeatingChecks


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 570

	def get_scenario_title(self):
		return 'District Heating: valve closes on high city return temperature'

	def get_scenario_description(self):
		return 'Если температура обратки в город выше допустимого значения в течение минуты, кран закрывается'

	def get_checklist_id(self):
		return '3.12.3'

	def run(self):
		self.run_valve_check('high_city_return')