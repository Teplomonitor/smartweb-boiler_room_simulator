'''
@author: admin
'''

import time
from copy import copy

import smartnet.message as sm

import smartnet.constants as snc
import programs.factory   as pf

from smartnet.message_log import MessageLogReader

from consoleLog import print_log   as print_log
from consoleLog import print_error as print_error


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
		self._last_entry = None
		
		self._initDone = True
	
	def clear(self):
		for prg in self._programList:
			prg.clear()
			
		self._activeProgramsList = []
		self._programList = []
		
		if self._gui:
			self._gui.clear()
			
	def initController(self, resetConfig, programPresetList):
		self.clear()
			
		if resetConfig:
			self.resetConfig()
			for program in programPresetList:
				if self.makeNewProgram(program) == False:
					print_error(f'Preset: program {program.get_type()}_{program.get_id()} make fail!')
					
				time.sleep(1)
		else:
			if not programPresetList:
				return
			
			if len(programPresetList) == 0:
				return
			
			activeProgramList = []
			i = 0
			while i < 3:
				activeProgramList.extend(self.readControllerProgramList())
				for program in programPresetList:
					programFound = self.searchProgramInActiveProgramList(program.get_id(), program.get_type(), activeProgramList)
					if not programFound:
						print_error(f'program {program.get_id()}.{program.get_type()} not found')
						i += 1
						break
					
				if programFound:
					print_log('all programs found')
					break
				
			if not programFound:
				print_error('controller got wrong preset')
				return
			
			for program in programPresetList:
				self.addProgramFromPreset(program)
		
	def addProgramFromPreset(self, program):
		prg = pf.createProgram(program)
		self.addProgram(prg)
		return prg
	
	def parseActiveProgramsList(self, response):
		if response is None:
			return False
		else:
			data = response.get_data()
			
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
				print(f'found prg {programId}.{programType}')
				self._activeProgramsList.append(prg)
			
			return True
			
	def readControllerProgramList(self):
		print_log('read controller programs list')
		sm.CanListener.subscribe(self)
		
		def generate_request():
			request = sm.Message(
			snc.ProgramType.CONTROLLER,
			self._controllerId,
			snc.ControllerFunction['GET_ACTIVE_PROGRAMS_LIST'],
			snc.requestFlag['REQUEST'])
			return request
		
		request = generate_request()
		request.send()

		request.send()
		time.sleep(3)
		
		sm.CanListener.unsubscribe(self)
		
		return self._activeProgramsList
	
	def read_message_log(self):
		reader = MessageLogReader(controller_id=self._controllerId)
		entries = reader.read_entries(max_entries=20, last_entry = self._last_entry)
		if len(entries):
			self._last_entry = entries[-1]
			
		return entries
	
	def searchProgramInActiveProgramList(self, programId, programType, activeProgramList = None):
		if activeProgramList is None:
			activeProgramList = self.readControllerProgramList()
		for ap in activeProgramList:
			if ap['id'] == programId and ap['type'] == snc.ProgramType[programType]:
				return True
		return False
	
	def sendProgramAddRequest(self, programType, programId, programScheme):
		print_log('Send program add request')
		def generate_request():
			request = sm.Message(
			snc.ProgramType.CONTROLLER,
			self._controllerId,
			snc.ControllerFunction['ADD_NEW_PROGRAM'],
			snc.requestFlag['REQUEST'],
			[	snc.ProgramType[programType],
				programId,
				snc.ProgramScheme[programScheme]
			])
			return request

		def generate_required_response():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			response.setData([snc.ProgramType[programType], programId])
			return response

		def handle_response():
			if response is None:
				print_error('Program add timeout')
				return False
			else:
				programAddStatus = {
					'STATUS_ADD_PROGRAM_OK'                 : 0,
					'STATUS_ADD_PROGRAM_WRONG_PROGRAM_TYPE' : 1,
					'STATUS_ADD_PROGRAM_TOO_MANY_PROGRAMS'  : 2,
					'STATUS_ADD_PROGRAM_UNDEFINED_ERROR'    : 3,
				}
				data = response.get_data()
				if data[2] == programAddStatus['STATUS_ADD_PROGRAM_OK']:
					print_log('Program add ok!')
					return True
				else:
					print_error('Program add error %d' %(data[2]))
					return False


		request        = generate_request()
		responseFilter = generate_required_response()

		response = request.send(responseFilter, 10)

		return handle_response()

	def makeNewProgram(self, preset):
		return preset.loadPreset(self)

	def get_program_list(self): return self._programList
	
	def on_can_message_received(self, msg):
		def generateResponse():
			response = sm.Message(
			snc.ProgramType.CONTROLLER,
			self._controllerId,
			snc.ControllerFunction['GET_ACTIVE_PROGRAMS_LIST'],
			snc.requestFlag['RESPONSE'])
			return response
		
		if msg.compare(generateResponse()):
			self.parseActiveProgramsList(msg)
			
	def resetConfig(self):
		print_log('send Controller reset request')
		def generate_request():
			request = sm.Message(
			snc.ProgramType.CONTROLLER,
			self._controllerId,
			snc.ControllerFunction['RESET_PROGRAMS'],
			snc.requestFlag['REQUEST'])
			return request

		def generate_required_response():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handle_response():
			if response is None:
				print_error('Program reset timeout')
				return False
			else:
				return True

		request        = generate_request()
		responseFilter = generate_required_response()

		i = 0
		while i < 3:
			response = request.send(responseFilter, 10)
			result = handle_response()
			if result:
				break;
			print_log('retry')
			i = i + 1
			
		return result


	def addProgram(self, program):
		print_log('add prg to list')
		self._programList.append(program)
		
		prg = {'id': program.get_id(), 'type': snc.ProgramType[program.get_type()]}
		
		self._activeProgramsList.append(prg)
		if self._gui:
			self._gui.addProgram(program)
	
	def get_outputs_num(self):
		return 0
	
	def get_inputs_num(self):
		return 0
