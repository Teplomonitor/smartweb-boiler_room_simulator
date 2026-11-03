from scenario.base.district_heating_reserve import DistrictHeatingReserveChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingReserveChecks):
	ESTIMATED_RUN_SECONDS = 600

	def get_scenario_title(self):
		return 'ИТП: догрев и резерв, авария города'

	def get_scenario_description(self):
		return 'При недогреве город работает совместно с котлом; авария города закрывает КЗР, сохраняя резерв.'

	def get_checklist_id(self):
		return '3.12.13'

	def get_default_preset(self):
		return 'district_heating_supplement'

	def run(self):
		self.run_reserve_mode_check(snc.DistrictHeatingReserveMode.SUPPLEMENT_AND_RESERVE)