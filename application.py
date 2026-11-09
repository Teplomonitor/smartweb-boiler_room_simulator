"""Application lifecycle. Physical models and transports remain separate services."""

import threading
from copy import copy


SHUTDOWN_TIMEOUT = 60.0


class Application:
	"""Own a single session; construction has no GUI, thread or network side effects."""

	def __init__(self, args, gui_factory=None, worker_factory=None):
		self.args = args
		self.gui = None
		self.worker = None
		self.stop_event = threading.Event()
		self._gui_factory = gui_factory
		self._worker_factory = worker_factory
		self._started = False
		self._shutdown_complete = False
		self.interactive_connection = getattr(args, 'interactive_connection', False)
		self.closing = False

	def start(self):
		import mainThread
		import consoleLog

		if self._started or self._shutdown_complete:
			raise RuntimeError('Application sessions cannot be restarted')
		mainThread.register_application(self)
		self._started = True
		try:
			if self.args.gui:
				factory = self._gui_factory
				if factory is None:
					from gui.frame import guiThread
					factory = guiThread
				self.gui = factory(self.args.profile)
			consoleLog.init_gui(self.gui)
			if self.interactive_connection:
				self.stop_event.set()
				self.gui.configure_connection(self)
				return
			factory = self._worker_factory or mainThread.ApplicationWorker
			self.worker = factory(self.args, self.gui, self.stop_event)
			self.worker.start()
		except BaseException:
			self.shutdown()
			raise

	def connect(self, settings):
		"""Start a connection from the GUI thread; transport setup runs in the worker."""
		import mainThread
		from connection_settings import validate_settings

		if not self.interactive_connection or self.closing or self._shutdown_complete:
			raise RuntimeError('Подключение сейчас недоступно.')
		settings = validate_settings(settings)
		if self.worker is not None:
			if self.worker.is_alive():
				raise RuntimeError('Дождитесь отключения предыдущего соединения.')
			if not self.worker.cleanup_complete:
				raise RuntimeError('Не все ресурсы освобождены. Перезапустите приложение.')
			mainThread.reset_connection_services()
		args = copy(self.args)
		args.id = settings['controller_id']
		args.can = settings['can_context'] if settings['transport'] == 'can' else 'virtual'
		args.udp = settings['udp_port'] if settings['transport'] == 'udp' else 0
		self.stop_event = threading.Event()
		factory = self._worker_factory or mainThread.ApplicationWorker
		try:
			self.worker = factory(args, self.gui, self.stop_event)
			self.worker.keep_gui_open = True
			self.worker.start()
		except BaseException:
			self.stop_event.set()
			raise

	def disconnect(self):
		"""Non-blocking cancellation; GUI polls completion before enabling reconnect."""
		self.stop_event.set()

	def request_stop(self):
		"""Non-blocking; safe to call from GUI event handlers and repeatedly."""
		self.closing = True
		self.stop_event.set()

	def shutdown(self, timeout=SHUTDOWN_TIMEOUT):
		"""Wait outside GUI callbacks. A timeout is reported, never a forced thread kill."""
		import mainThread
		from consoleLog import print_error

		if self._shutdown_complete:
			return True
		self.request_stop()
		if self.worker and self.worker.ident is not None:
			if self.worker is threading.current_thread():
				return False
			self.worker.join(timeout)
			if self.worker.is_alive():
				print_error('Application worker did not stop before the timeout')
				return False
		if self.gui and (self.interactive_connection or not self.worker or self.worker.ident is None):
			self.gui.stop()
		mainThread.unregister_application(self)
		self._shutdown_complete = True
		return True