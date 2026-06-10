'''
@author: admin
'''

import os
from copy import copy


import smartnet.constants as snc

import smartnet.remoteControl  as sr
import smartnet.message        as sm

from smartnet.channelMapping import InputChannel     as InputChannel
from smartnet.channelMapping import OutputChannel    as OutputChannel

from consoleLog import printLog   as printLog
from consoleLog import printError as printError

class ParameterInfo(object):
	def __init__(self,
				programType,
				parameterId):
		self._programType = programType
		self._parameterId = parameterId
	
	def getProgramType(self): return self._programType
	def getParameterId(self): return self._parameterId

class Program(object):
	'''
	classdocs
	'''

	def getType(self): return 'PROGRAM'
	
	def getInputTitles(self):
		return [
			]

	def getOutputTitles(self):
		return [
			]

	def getInputsNum (self): return len(self.getInputTitles ())
	def getOutputsNum(self): return len(self.getOutputTitles())
	
	def initInputs(self, inputMappings = None):
		self._inputs  = []
		
		inputTitle     = self.getInputTitles()
		
		channelNum = self.getInputsNum()
		
		for i in range(channelNum):
			channel = InputChannel()
			channel.setTitle(inputTitle[i])
			if inputMappings:
				channel.setMapping(inputMappings[i])
			self._inputs.append(channel)
			
	
	def initOutputs(self, outputMappings = None):
		self._outputs = []
		
		outputTitle = self.getOutputTitles()
		
		channelNum = self.getOutputsNum()
		
		for i in range(channelNum):
			channel = OutputChannel()
			channel.setTitle(outputTitle[i])
			if outputMappings:
				channel.setMapping(outputMappings[i])
				
			self._outputs.append(channel)
			
			if self._outputs[i].isMapped():
				self.readOutput(i)
	
	def initGuiParameters(self):
		pass
	
	def __init__(self, preset):
		'''
		Constructor
		'''
		
		self._preset  = preset
		
		if preset:
			self.setScheme(preset.getScheme())
			self.setId    (preset.getId()    )
			self.setTitle (preset.getTitle() )
			
			self.initInputs (preset.getInputs ())
			self.initOutputs(preset.getOutputs())
		else:
			self.setScheme('DEFAULT')
			self.setId    (1)
			self.setTitle ('Program')
			
			self.initInputs ()
			self.initOutputs()
			

		self._parameters = {}
		
		self.initGuiParameters()
		
		self.CanSubscribe()
	
	def getMaxPower(self):
		if 'max_power' in self._parameters:
			return self._parameters['max_power'].getValue()
		return 0
	
	def getMaxFlowRate(self):
		if 'max_flow_rate' in self._parameters:
			return self._parameters['max_flow_rate'].getValue()
		return 0

	def Clear(self):
		self.CanUnSubscribe()
		self._inputs  = []
		self._outputs = []
		self._parameters = {}
		
	
	def CanSubscribe(self):
		sm.CanListener.subscribe(self)
		
	def CanUnSubscribe(self):
		sm.CanListener.unsubscribe(self)
		
	def __del__(self):
		self.CanUnSubscribe()
		print(f'kill {self.getTitle()}')
		
	def OnCanMessageReceived(self, msg):
		headerOk = (
					(msg.getProgramId  () == self.getId()) and
					(msg.getProgramType() == snc.ProgramType['REMOTE_CONTROL']) and
					(msg.getFunctionId () == snc.RemoteControlFunction['GET_PARAMETER_VALUE']) and
					(msg.getRequestFlag() == snc.requestFlag['RESPONSE']))

		if headerOk:
			data   = msg.getData()
			dataOk = (
				(data[0] == snc.ProgramType['PROGRAM']) and
				(data[1] == snc.ProgramParameter['OUTPUT']['id']))
			
			if dataOk:
				outputId    = data[2]
				outputValue = data[3]
				
				if outputId < len(self._outputs):
					self.setOutputValue(outputId, outputValue)
		
		
	def getInputs(self   ): return self._inputs
	def getInputChannel (self, i): return self._inputs [i]
	def setInput (self, i, value): self._inputs [i] = value
	
	def getOutputs(self   ): return self._outputs
	def getOutputChannel (self, i): return self._outputs[i]
	def setOutputChannel (self, i, channel): self._outputs[i] = channel
	def setOutputValue   (self, i, value): self.getOutputChannel(i).setValue(value)
	
	def getParameters(self): return self._parameters
	
	def getInputTitle (self, i): return self.getInputTitles ()[i]
	def getOutputTitle(self, i): return self.getOutputTitles()[i]

	def getScheme   (self): return self._scheme
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	
	def setScheme(self, scheme   ): self._scheme = scheme
	def setId    (self, programId): self._id     = programId
	def setTitle (self, title    ): self._title  = title
	
	def getPreset   (self): return self._preset
	def getGuiColor (self): return 'default'

	def disableGuiControl(self):
		for prgInput in self._inputs:
			prgInput.disableGuiControl()
			
	def enableGuiControl(self):
		for prgInput in self._inputs:
			prgInput.enableGuiControl()
		
	def bindInput(self, channel_id, mapping):
		printLog(f'bind program input {channel_id}')
		def generateRequest():
			request = sm.Message(
			snc.ProgramType['REMOTE_CONTROL'],
			self.getId(),
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['INPUT_MAPPING']['id'], channel_id, mapping.getRaw(0), mapping.getRaw(1)])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				printError('bind input timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					printLog('bind ok!')
					return True
				else:
					printError('bind error %d' %(result))
					return False
				
		
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

	def bindOutput(self, channel_id, mapping):
		printLog(f'bind program output {channel_id}')
		def generateRequest():
			request = sm.Message(
			snc.ProgramType['REMOTE_CONTROL'],
			self.getId(),
			snc.RemoteControlFunction['SET_PARAMETER_VALUE'],
			snc.requestFlag['REQUEST'],
			[snc.ProgramType['PROGRAM'], snc.ProgramParameter['OUTPUT_MAPPING']['id'], channel_id, mapping.getRaw(0), mapping.getRaw(1)])
			return request

		def generateRequiredResponse():
			response = copy(request)
			response.setRequestFlag(snc.requestFlag['RESPONSE'])
			return response

		def handleResponse():
			if response is None:
				printError('bind output timeout')
				return False
			else:
				data = response.getData()
				resultPos = len(data) - 1
				result = data[resultPos]
				if result == snc.RemoteControlSetParameterResult['SET_PARAMETER_STATUS_OK']:
					printLog('bind ok!')
					return True
				else:
					printError('bind error %d' %(result))
					return False
				
		
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
	
	def readOutput(self, outputId):
		param = sr.RemoteControlParameter(
			'PROGRAM', 'OUTPUT',
			parameterIndex = outputId,
			programId = self.getId())
		
		value = None
		if param.read():
			value = param.getValue()
			self.setOutputValue(outputId, value)
			
		return value
	
	def getParameterInfo(self, parameter):
		return None
	
	def readParameterValue(self, parameter):
		p = self.getParameterInfo(parameter)
		if p is None:
			return None
		remoteParam = sr.RemoteControlParameter(parameterInfo = p, programId = self.getId() )
		remoteParam.read()
		
		return remoteParam.getValue()
	
	def writeParameterValue(self, parameter, value, index = None, confirm = True):
		p = self.getParameterInfo(parameter)
		if p is None:
			return None
		
		remoteParam = sr.RemoteControlParameter(
			parameterInfo = p,
			programId = self.getId(),
			parameterValue = value,
			parameterIndex = index
		)
		
		remoteParam.write(confirm)
		
		return remoteParam.getValue()
	
	def setInputsRange(self, inputsRange):
		i = 0
		for inputRange in inputsRange:
			if inputRange:
				self._inputs[i].setMin(inputRange[0])
				self._inputs[i].setMax(inputRange[1])
			i = i + 1

	def saveLog(self, logDir = None):
		titleCommon = self.getTitle() + '_' + str(self.getId())
		
		if logDir:
			titleCommon = os.path.join(logDir, titleCommon)
		
		logDirInputs  = os.path.join(titleCommon, 'inputs')
		logDirOutputs = os.path.join(titleCommon, 'outputs')
		
		for programInput in self._inputs:
			programInput.saveLog(logDirInputs)
		for programOutput in self._outputs:
			programOutput.saveLog(logDirOutputs)
	
	# TODO: move to derived consumer class
	def getTemperatureSource(self):
		preset = self.getPreset()
		settings = preset.getSettings().get()
		for setting in settings:
			if setting.getProgramType() == 'CONSUMER' and setting.getParameterIdCode() == 'GENERATOR_ID':
				return setting.getValue()
		return 0
	
	def getTemperatureSourceList(self):
		return [self.getTemperatureSource()]
	
	