
from functions.timeOnDelay  import TimeOnDelay  as TimeOnDelay
from functions.timeOffDelay import TimeOffDelay as TimeOffDelay

class TimeOnOffDelay(object):
	def __init__(self):
		self._onDelay  = TimeOnDelay ()
		self._offDelay = TimeOffDelay()

	def Get(self, value,  onDelay, offDelay):
		return self._onDelay.Get(self._offDelay.Get(value, offDelay), onDelay)

	def TimerReset(self):
		self._onDelay .TimerReset()
		self._offDelay.TimerReset()

