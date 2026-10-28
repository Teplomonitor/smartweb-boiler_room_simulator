from scenario.base.journal import JournalCanEmitter, JournalScenarioMixin
from scenario.scenario import Scenario as Parent
from smartnet.message import Message
import smartnet.constants as snc


class JournalCollisionScenario(JournalScenarioMixin, Parent):
	JOURNAL_TIMEOUT = 45
	QUIET_PERIOD = 23

	def get_required_programs(self):
		return {'boiler': snc.ProgramType.BOILER}

	def get_default_preset(self):
		return 'boiler_3_5_2'

	def force_preset_load(self):
		return True

	def make_collision_emitter(self):
		program_id = self._programList['boiler'].get_id()
		controller_id = self._controllerHost.get_controller_id()
		# The controller chooses a random marker from 1..255; two different
		# markers ensure that at least one is different from its own marker.
		responses = [
			Message(
				snc.ProgramType.PROGRAM, program_id,
				snc.ProgramFunction['I_AM_PROGRAM'], snc.RequestFlag.RESPONSE,
				[marker, controller_id, snc.ProgramType.BOILER],
			)
			for marker in (1, 2)
		]
		return JournalCanEmitter(responses)