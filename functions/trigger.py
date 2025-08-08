


class RisingEdgeTrigger(object):
	def __init__(self):
		self._previousStateSetup = False

	def Get(self, value):
		if value and not self._previousStateSetup:
			self._previousStateSetup = True;
			return True
		
		if not value:
			self._previousStateSetup = False
		
		return False

class FallingEdgeTrigger(object):
	def __init__(self):
		self._previousStateSetup = False

	def Get(self, value):
		if not value and self._previousStateSetup:
			self._previousStateSetup = False;
			return True
		
		if value:
			self._previousStateSetup = True
		
		return False
