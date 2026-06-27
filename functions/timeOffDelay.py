
import time

def getOutput(inputValue, outputValue, delay, elapsedTime):
	if inputValue or (outputValue and (elapsedTime < delay)):
		return True
	return False

class TimeOffDelay(object):
	def __init__(self):
		self._out = False
		self._offTime = time.time()

	def Get(self, value, offDelay):
		if value:
			self._offTime = time.time()
		
		self._out = getOutput(value, self._out, offDelay, self.get_cropped_elapsed_time(offDelay))
		
		return self._out
	
	def get_cropped_elapsed_time(self, delay):
		now = time.time()
		if now - self._offTime > delay:
			self._offTime = now - delay
		
		if self._out:
			return now - self._offTime;
		else:
			return 0

	def reset(self):
		self._offTime = time.time()
		self._out = False

