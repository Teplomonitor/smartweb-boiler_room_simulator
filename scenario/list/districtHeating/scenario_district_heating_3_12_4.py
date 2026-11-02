from scenario.base.district_heating_checks import DistrictHeatingChecks


class Scenario(DistrictHeatingChecks):
	ESTIMATED_RUN_SECONDS = 570

	def get_scenario_title(self):
		return 'District Heating: high house return blocks valve closing'

	def get_scenario_description(self):
		return 'Если обратка из дома выше допустимого значения, высокая обратка в город не должна закрывать кран'

	def get_checklist_id(self):
		return '3.12.4'

	def run(self):
		self.run_valve_check('high_house_return')