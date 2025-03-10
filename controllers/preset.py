

import smartnet.constants as snc
import controllers.defaultPreset
from programs.program import Program as Program

class ProgramPreset(object):
	'''
	classdocs
	'''
	
	def __init__(self,
			programType, programScheme, programId,
			programTitle, programSettings, programInputs, programOutputs):
		self._type      = programType
		self._scheme    = programScheme
		self._id        = programId
		self._title     = programTitle
		self._settings  = programSettings
		self._inputs    = programInputs
		self._outputs   = programOutputs

	def getType     (self): return self._type
	def getScheme   (self): return self._scheme
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	def getSettings (self): return self._settings
	def getInputs   (self): return self._inputs
	def getOutputs  (self): return self._outputs

	def loadPreset(self, controller):
		result = controller.sendProgramAddRequest(self._type, self._id, self._scheme)
		if not result:
			print('Program %s add fail'%(self._title))
			return False

		prg = Program(self._type, self._id, self._scheme)
		controller.addProgram(prg)

		if self._inputs:
			i = 0
			for inputMapping in self._inputs:
				if inputMapping:
					prg.bindInput(i, inputMapping)
				i = i + 1





def getPresetsList():
	return controllers.defaultPreset.getPresetsList()