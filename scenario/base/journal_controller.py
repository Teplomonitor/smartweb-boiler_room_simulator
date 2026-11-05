import threading

from consoleLog import print_error
from scenario.base.journal import JournalCanEmitter, JournalScenarioMixin
from scenario.scenario import Scenario as Parent
from smartnet.message import CanListener, Message
import smartnet.constants as snc


class ControllerPresenceCollector:
	def __init__(self):
		self._ids = set()
		self._lock = threading.Lock()

	def on_can_message_received(self, message):
		if (message is not None and message.get_program_type() == snc.ProgramType.CONTROLLER
				and message.getRequestFlag() == snc.RequestFlag.RESPONSE):
			with self._lock:
				self._ids.add(message.getProgramId())

	def get_ids(self):
		with self._lock:
			return set(self._ids)


class JournalControllerScenario(JournalScenarioMixin, Parent):
	CAN_BROADCAST_ID = 0
	DISCOVERY_SECONDS = 12
	ANNOUNCEMENT_SECONDS = 12
	ANNOUNCEMENT_INTERVAL = 1
	CONNECTION_LOSS_SECONDS = 5 * 60
	JOURNAL_TIMEOUT = 60

	def find_unused_controller_id(self):
		collector = ControllerPresenceCollector()
		CanListener.subscribe(collector)
		try:
			Message(
				snc.ProgramType.CONTROLLER, self.CAN_BROADCAST_ID,
				snc.ControllerFunction.I_AM_HERE, snc.RequestFlag.REQUEST,
			).send()
			self.wait(self.DISCOVERY_SECONDS)
		finally:
			CanListener.unsubscribe(collector)
		occupied = collector.get_ids()
		occupied.add(self._controllerHost.get_controller_id())
		occupied.update(controller.get_id() for controller in self._sim.getControllersIOList())
		# CAN programNumber is eight bits; zero is the broadcast address.
		for controller_id in range(255, self.CAN_BROADCAST_ID, -1):
			if controller_id not in occupied:
				return controller_id
		print_error('На CAN нет свободного номера для тестового контроллера')
		return None

	def make_presence_emitter(self, controller_id):
		message = Message(
			snc.ProgramType.CONTROLLER, controller_id,
			snc.ControllerFunction.I_AM_HERE, snc.RequestFlag.RESPONSE,
			[snc.ControllerType.SWK_1],
		)
		return JournalCanEmitter([message], interval=self.ANNOUNCEMENT_INTERVAL)
