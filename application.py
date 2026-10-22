"""Application lifecycle. Physical models and transports remain separate services."""

import threading


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
			factory = self._worker_factory or mainThread.ApplicationWorker
			self.worker = factory(self.args, self.gui, self.stop_event)
			self.worker.start()
		except BaseException:
			self.shutdown()
			raise

	def request_stop(self):
		"""Non-blocking; safe to call from GUI event handlers and repeatedly."""
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
		elif self.gui:
			self.gui.stop()
		mainThread.unregister_application(self)
		self._shutdown_complete = True
		return True