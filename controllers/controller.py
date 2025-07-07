'''
@author: admin
'''

import time
from copy import copy

from smartnet.message import Message as smartnetMessage
import smartnet.constants as snc
from programs.factory import createProgram as createProgram

from consoleLog import printLog   as printLog
from consoleLog import printError as printError


class Controller(object):
	'''
	classdocs
	'''
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(Controller, cls).__new__(cls)
		return cls.instance

	def __init__(self, controllerId = None, gui = None):
		'''
		Constructor
		'''
		if hasattr(self, '_initDone'):
			return
		
		self._programList = []
		self._controllerId = controllerId
		self._gui = gui
		
		self._initDone = True
	
	def Clear(self):
		for prg in self._programList:
			prg.Clear()
			
		self._programList = []
		
		if self._gui:
			self._gui.Clear()
			
	def initController(self, resetConfig, programPresetList):
		self.Clear()
			
		if resetConfig:
			self.resetConfig()
			for program in programPresetList:
				if self.makeNewProgram(program) == False:
					printError(f'Preset: program {program.getType()}_{program.getId()} make fail!')
					
				time.sleep(2)
		else:
			for program in programPresetList:
				self.addProgramFromPreset(program)
		
	def addProgramFromPreset(self, program):
		prg = createProgram(program)
		self.addProgram(prg)
		return prg
		
	def sendProgramAddRequest(self, programType, programId, programScheme):
		printLog('Send program add request')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			snc.requestFlag['REQUEST'],
			[programType, programId, programScheme])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			response.setData([programType, programId])
			return response

		def handleResponse():
			if response is None:
				printError('Program add timeout')
				return False
			else:
				programAddStatus = {
					'STATUS_ADD_PROGRAM_OK'                 : 0,
					'STATUS_ADD_PROGRAM_WRONG_PROGRAM_TYPE' : 1,
					'STATUS_ADD_PROGRAM_TOO_MANY_PROGRAMS'  : 2,
					'STATUS_ADD_PROGRAM_UNDEFINED_ERROR'    : 3,
				}
				data = response.getData()
				if data[2] == programAddStatus['STATUS_ADD_PROGRAM_OK']:
					printLog('Program add ok!')
					return True
				else:
					printError('Program add error %d' %(data[2]))
					return False


		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		response = request.send(responseFilter, 30)

		return handleResponse()

	def makeNewProgram(self, preset):
		return preset.loadPreset(self)

	def getProgramList(self): return self._programList

	def resetConfig(self):
		printLog('send Controller reset request')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['RESET_PROGRAMS'],
			snc.requestFlag['REQUEST'])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				printError('Program reset timeout')
				return False
			else:
				return True

		request        = generateRequest()
		responseFilter = generateRequiredResponse()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handleResponse()
			if result:
				break;
			printLog('retry')
			i = i + 1
			
		return result


	def addProgram(self, program):
		printLog('add prg to list')
		self._programList.append(program)
		if self._gui:
			self._gui.addProgram(program)
	
	def getOutputsNum(self):
		return 0
	
	def getInputsNum(self):
		return 0
