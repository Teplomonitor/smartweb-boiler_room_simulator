'''
@author: admin
'''

import time
from copy import copy

from smartnet.message import CanListener as CanListener
from smartnet.message import Message     as smartnetMessage

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
		
		self._activeProgramsList = []
		self._programList = []
		self._controllerId = controllerId
		self._gui = gui
		
		self._initDone = True
	
	def Clear(self):
		for prg in self._programList:
			prg.Clear()
			
		self._activeProgramsList = []
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
			activeProgramList = []
			i = 0
			while i < 3:
				activeProgramList.extend(self.readControllerProgramList())
				for program in programPresetList:
					programFound = self.searchProgramInActiveProgramList(program.getId(), program.getType(), activeProgramList)
					if not programFound:
						printError(f'program {program.getId()} not found')
						i += 1
						break
					
				if programFound:
					printLog('all programs found')
					break
				
			if not programFound:
				printError('controller got wrong preset')
				return
			
			for program in programPresetList:
				self.addProgramFromPreset(program)
		
	def addProgramFromPreset(self, program):
		prg = createProgram(program)
		self.addProgram(prg)
		return prg
	
	def parseActiveProgramsList(self, response):
		if response is None:
			return False
		else:
			data = response.getData()
			
			programNum = int(len(data) / 2)
			
			for i in range(programNum):
				programId   = data[i*2  ]
				programType = data[i*2+1]
				
				if programId == 0:
					break
				
				skip = False
				for prg in self._activeProgramsList:
					if prg['id'] == programId:
						skip = True
						break

				if skip:
					continue
				
				prg = {'id': programId, 'type': programType}
				print(f'found prg {programId}')
				self._activeProgramsList.append(prg)
			
			return True
			
	def readControllerProgramList(self):
		printLog('read controller programs list')
		CanListener.subscribe(self)
		
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['GET_ACTIVE_PROGRAMS_LIST'],
			snc.requestFlag['REQUEST'])
			return request
		
		request = generateRequest()
		request.send()

		request.send()
		time.sleep(3)
		
		CanListener.unsubscribe(self)
		
		return self._activeProgramsList
	
	def searchProgramInActiveProgramList(self, programId, programType, activeProgramList = None):
		if activeProgramList is None:
			activeProgramList = self.readControllerProgramList()
		for ap in activeProgramList:
			if ap['id'] == programId and ap['type'] == snc.ProgramType[programType]:
				return True
		return False
	
	def sendProgramAddRequest(self, programType, programId, programScheme):
		printLog('Send program add request')
		def generateRequest():
			request = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			snc.requestFlag['REQUEST'],
			[	snc.ProgramType[programType],
				programId,
				snc.ProgramScheme[programScheme]
			])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			response.setData([snc.ProgramType[programType], programId])
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
	
	def OnCanMessageReceived(self, msg):
		def generateResponse():
			response = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			self._controllerId,
			snc.ControllerFunction['GET_ACTIVE_PROGRAMS_LIST'],
			snc.requestFlag['RESPONSE'])
			return response
		
		if msg.compare(generateResponse()):
			self.parseActiveProgramsList(msg)
			
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
		
		prg = {'id': program.getId(), 'type': snc.ProgramType[program.getType()]}
		
		self._activeProgramsList.append(prg)
		if self._gui:
			self._gui.addProgram(program)
	
	def getOutputsNum(self):
		return 0
	
	def getInputsNum(self):
		return 0
