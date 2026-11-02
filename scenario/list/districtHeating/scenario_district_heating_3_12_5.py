from scenario.base.district_heating_checks import DistrictHeatingChecks


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 360

	def get_scenario_title(self):
		return 'District Heating: valve closes when city return is hotter than supply'

	def get_scenario_description(self):
		return (
			'Если температура обратки в город выше температуры подачи в город '
			'в течение двух минут, кран закрывается'
		)

	def get_checklist_id(self):
		return '3.12.5'

	def run(self):
		self.run_valve_check('reversed_city_flow')