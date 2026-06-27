
import time


class TimeOnDelay(object):
	"""A small helper to detect when an input stays True for a specified delay.

	Backwards-compatible API (methods with PascalCase) is preserved because
	other modules call these methods. New, Pythonic snake_case aliases are
	provided as well.

	Usage:
	  tod = TimeOnDelay()
	  # inside a loop:
	  if tod.get(value, on_delay_seconds):
		  # value has been True for at least on_delay_seconds

	Notes on behavior:
	  - On first call get(...) will reset the internal timer.
	  - get_cropped_elapsed_time() returns the measured elapsed time; it updates
		the internal elapsed time while the output is not yet True.
	  - reset() resets the internal state and restarts timing from now.
	"""

	def __init__(self) -> None:
		# True when the delay condition is already met
		self._out: bool = False
		# reference time when the current True run started
		self._on_time: float = time.time()
		# cached elapsed time (seconds)
		self._elapsed_time: float = 0.0
		# mark that we haven't run the timer reset on the first get() call
		self._first_start: bool = True

	def get(self, value: bool, on_delay: float, manual_reset: bool = False) -> bool:
		"""Evaluate the on-delay behavior.

		If `value` remains True for at least `on_delay` seconds, the method
		returns True. When `value` becomes False the timer is either paused
		(if manual_reset=True) or reset.
		"""
		if self._first_start:
			# initialize timing on the first real use
			self._first_start = False
			self.reset()

		if value:
			self._out = self.get_cropped_elapsed_time() >= on_delay
		else:
			self._out = False
			now = time.time()
			if manual_reset:
				# keep elapsed_time but shift on_time so that elapsed remains
				# the same relative to now
				self._on_time = now - self._elapsed_time
			else:
				# clear accumulated elapsed time and start counting from now
				self._elapsed_time = 0.0
				self._on_time = now

		return self._out

	def get_cropped_elapsed_time(self) -> float:
		"""Return the current elapsed time for the active True period.

		While the output state is False this method updates the internal
		elapsed time so callers can inspect progress toward the on-delay.
		"""
		if not self._out:
			self._elapsed_time = time.time() - self._on_time

		return self._elapsed_time

	def reset(self) -> None:
		"""Reset internal state and restart timing from now."""
		self._out = False
		self._elapsed_time = 0.0
		self._on_time = time.time()
