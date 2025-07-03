from os.path import dirname, basename, isfile, join
import glob

import smartnet.constants as snc

from programs.factory import createProgram as createProgram

class ProgramPreset(object):
	'''
	classdocs
	'''
	
	def __init__(self,
			programType, programScheme, programId,
			programTitle, programSettings, programInputs, programOutputs, power):
		self._type      = programType
		self._scheme    = programScheme
		self._id        = programId
		self._title     = programTitle
		self._settings  = programSettings
		self._inputs    = programInputs
		self._outputs   = programOutputs
		self._power     = power

	def getType     (self): return self._type
	def getScheme   (self): return self._scheme
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	def getSettings (self): return self._settings
	def getInputs   (self   ): return self._inputs
	def getInput    (self, i): return self._inputs[i]
	def getOutputs  (self   ): return self._outputs
	def getOutput   (self, i): return self._outputs[i]
	def getPower    (self): return self._power


	def loadPreset(self, controller):
		prgType   = snc.ProgramType  [self._type]
		prgScheme = snc.ProgramScheme[self._scheme]

		result = controller.sendProgramAddRequest(prgType, self._id, prgScheme)

		if not result:
			print('Program %s add fail'%(self._title))
			return False

		prg = createProgram(self)
		controller.addProgram(prg)
		if self._inputs:
			i = 0
			for value in self._inputs:
				if value:
					prg.bindInput(i, value)
				i = i + 1

		if self._outputs:
			i = 0
			for value in self._outputs:
				if value:
					prg.bindOutput(i, value)
				i = i + 1

		if self._settings:
			for value in self._settings.get():
				value.setProgramId(self._id)
				value.write()

class ControllerPreset(object):
	'''
	classdocs
	'''
	def __init__(self,
			programType, programId,
			programTitle):
		self._type      = programType
		self._id        = programId
		self._title     = programTitle

	def getType     (self): return self._type
	def getId       (self): return self._id
	def getTitle    (self): return self._title


def getPresetsList(presetId):
	regex = join(dirname(__file__),'list', "*.py")
	moduleId = 'presets.list.%s' % presetId
	
	modules = glob.glob(regex)
	__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
	
	if presetId in __all__:
		preset_module = __import__(moduleId, fromlist=["presets.list"])

		return preset_module.getPresetsList()
	
	print(f'wrong preset {presetId}')
	return None
