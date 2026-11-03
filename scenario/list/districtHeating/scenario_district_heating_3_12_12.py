from scenario.base.district_heating_reserve import DistrictHeatingReserveChecks
import smartnet.constants as snc


class Scenario(DistrictHeatingReserveChecks):
	ESTIMATED_RUN_SECONDS = 600

	def get_scenario_title(self):
		return 'ИТП: только резерв, изоляция города и краны котла'

	def get_scenario_description(self):
		return 'Недогрев включает резерв после закрытия КЗР; авария города удерживает изоляцию; снятие запроса закрывает краны.'

	def get_checklist_id(self):
		return '3.12.12'

	def get_default_preset(self):
		return 'district_heating_reserve'

	def run(self):
		self.run_reserve_mode_check(snc.DistrictHeatingReserveMode.RESERVE_ONLY)