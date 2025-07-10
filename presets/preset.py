from os.path import dirname, basename, isfile, join
import glob

import smartnet.constants as snc

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

	def addProgramToControllerHost(self, controller):
		i = 0
		while i < 3:
			result = controller.sendProgramAddRequest(self._type, self._id, self._scheme)
			
			if result:
				return True
			else:
				programFound = controller.searchProgramInActiveProgramList(self._id, self._type)
				
				if programFound:
					print('Program %s found on controller, probably message was lost'%(self._title))
					return True
				else:
					print('controller add program retry')
					i += 1
					continue
		return False

	def bindInputs(self, prg):
		if self._inputs:
			i = 0
			for value in self._inputs:
				if value:
					prg.bindInput(i, value)
				i = i + 1

	def bindOutputs(self, prg):
		if self._outputs:
			i = 0
			for value in self._outputs:
				if value:
					prg.bindOutput(i, value)
				i = i + 1

	def loadSettings(self):
		if self._settings:
			for value in self._settings.get():
				value.setProgramId(self._id)
				value.write()
				
	def loadPreset(self, controller):
		programAddOk = self.addProgramToControllerHost(controller)
		
		if not programAddOk:
			print('Program %s add fail'%(self._title))
			return False
		
		prg = controller.addProgramFromPreset(self)

		self.bindInputs (prg)
		self.bindOutputs(prg)
		self.loadSettings()

class ControllerPreset(object):
	'''
	classdocs
	'''
	def __init__(self,
			controllerType, controllerId,
			controllerTitle):
		self._type      = controllerType
		self._id        = controllerId
		self._title     = controllerTitle

	def getType     (self): return self._type
	def getId       (self): return self._id
	def getTitle    (self): return self._title

def getPresetFilesList():
	regex = join(dirname(__file__),'list', "*.py")
	
	modules = glob.glob(regex)
	__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
	return __all__

def getPresetsList(presetId):
	moduleId = 'presets.list.%s' % presetId
	
	__all__ = getPresetFilesList()
	
	if presetId in __all__:
		preset_module = __import__(moduleId, fromlist=["presets.list"])

		return preset_module.getPresetsList()
	
	print(f'wrong preset {presetId}')
	return None
