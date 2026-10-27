from os.path import dirname, basename, isfile, join
import glob
import smartnet.constants as snc


def validate_program_presets(programs):
	ids = [program.get_id() for program in programs]
	if len(ids) != len(set(ids)):
		raise ValueError('Program IDs must be unique within a preset')
	virtual_outdoor = False
	for program in programs:
		if not program.is_virtual():
			continue
		if program.get_type() != snc.ProgramType.OUTDOOR_SENSOR:
			raise ValueError(f'Virtual program type is not implemented: {program.get_type()}')
		if program.getSettings() is not None or any(program.get_outputs()):
			raise ValueError('Virtual outdoor programs do not support controller settings or outputs')
		virtual_outdoor = True
	if virtual_outdoor and sum(program.get_type() == snc.ProgramType.OUTDOOR_SENSOR for program in programs) != 1:
		raise ValueError('A virtual outdoor source cannot coexist with another outdoor program')

class ProgramPreset(object):
	'''
	classdocs
	'''
	
	def __init__(self,
			programType, programScheme, programId,
			programTitle, programSettings, programInputs, programOutputs, execution='real'):
		if execution not in ('real', 'virtual'):
			raise ValueError(f'Unknown program execution mode: {execution}')
		self._execution = execution
		self._type      = programType
		self._scheme    = programScheme
		self._id        = programId
		self._title     = programTitle
		self._settings  = programSettings
		self._inputs    = programInputs
		self._outputs   = programOutputs

	def get_type     (self): return self._type
	def get_scheme   (self): return self._scheme
	def get_id       (self): return self._id
	def get_title    (self): return self._title
	def getSettings (self): return self._settings
	def get_inputs   (self   ): return self._inputs
	def getInput    (self, i): return self._inputs[i]
	def get_outputs  (self   ): return self._outputs
	def getOutput   (self, i): return self._outputs[i]

	def is_virtual(self): return self._execution == 'virtual'
	def get_execution(self): return self._execution

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

	def bind_inputs(self, prg):
		if self._inputs:
			i = 0
			for value in self._inputs:
				if value:
					prg.bind_input(i, value)
				i = i + 1

	def bind_outputs(self, prg):
		if self._outputs:
			i = 0
			for value in self._outputs:
				if value:
					prg.bind_output(i, value)
				i = i + 1

	def loadSettings(self):
		if self._settings:
			for value in self._settings.get():
				value.setProgramId(self._id)
				value.write()
				
	def loadPreset(self, controller):
		if self.is_virtual():
			validate_program_presets([self])
			controller.addProgramFromPreset(self)
			return True
		programAddOk = self.addProgramToControllerHost(controller)
		
		if not programAddOk:
			print('Program %s add fail'%(self._title))
			return False
		
		prg = controller.addProgramFromPreset(self)

		self.bind_inputs (prg)
		self.bind_outputs(prg)
		self.loadSettings()
		return True

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

	def get_type     (self): return self._type
	def get_id       (self): return self._id
	def get_title    (self): return self._title

def get_presetFilesList():
	regex = join(dirname(__file__),'list', "*.py")
	
	modules = glob.glob(regex)
	__all__ = [ basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
	return __all__

def get_presets_list(presetId):
	moduleId = 'presets.list.%s' % presetId
	
	__all__ = get_presetFilesList()
	
	if presetId in __all__:
		preset_module = __import__(moduleId, fromlist=["presets.list"])

		return preset_module.get_presets_list()
	
	print(f'wrong preset {presetId}')
	return None
