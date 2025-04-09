'''
Created on 9 апр. 2025 г.

@author: admin
'''

import time
from smartnet.message import Message as smartnetMessage
from controllers.channelMapping import Channel as Channel
import smartnet.constants as snc

def reportOutputMapping(controllerId, outputId, mapping):
	if mapping is None: return False

	msg = smartnetMessage(
			snc.ProgramType['CONTROLLER'],
			controllerId,
			snc.ControllerFunction['GET_RELAY_MAPPING'],
			snc.requestFlag['RESPONSE'],
			[outputId, mapping.getRaw(0), mapping.getRaw(1)])
	
	msg.send()
	return True

def sendImHere(controllerId, controllerType):
	msg = smartnetMessage(
		snc.ProgramType['CONTROLLER'],
		controllerId,
		snc.ControllerFunction['I_AM_HERE'],
		snc.requestFlag['RESPONSE'],
		[snc.ControllerType[controllerType],]
		)
	msg.send()
	
	
class ControllerIO(object):
	'''
	classdocs
	'''


	def __init__(self, controllerId, controllerType, controllerTitle):
		'''
		Constructor
		'''
		self._type      = controllerType
		self._id        = controllerId
		self._title     = controllerTitle
		self._time_start = time.time()
		
		self._input      = [Channel(None, None)] * self.getInputNumber()
		self._output     = [Channel(None, None)] * self.getOutputNumber()
		
		sendImHere(self.getId(), self.getType())
		self.reportChannelNumber()

	def getType     (self): return self._type
	def getId       (self): return self._id
	def getTitle    (self): return self._title
	
	
#	switch (type)
#	{
#		case eControllerType::STDC          :  m_inChCount =  3; m_outChCount =  2; break;
#		case eControllerType::LTDC_S40      :  m_inChCount = 10; m_outChCount =  5; break;
#		case eControllerType::XHCC          :  m_inChCount = 17; m_outChCount = 11; break;
#		case eControllerType::SWN           :  m_inChCount =  3; m_outChCount =  5; break;
#		case eControllerType::SWD           :  m_inChCount =  6; m_outChCount =  8; break;
#		case eControllerType::CALEON        :  m_inChCount =  2; m_outChCount =  2; break;
#		case eControllerType::XHCC_S62      :  m_inChCount = 18; m_outChCount = 11; break;
#		case eControllerType::LTDC_S45      :  m_inChCount = 10; m_outChCount =  6; break;
#		case eControllerType::SWK           :  m_inChCount =  6; m_outChCount =  7; break;
#		case eControllerType::SWK_1         :  m_inChCount =  6; m_outChCount =  8; break;
#		case eControllerType::CWC_CAN       :  m_inChCount = 20; m_outChCount = 10; break;
#		case eControllerType::ROOMIX_CAN    :  m_inChCount = 20; m_outChCount = 10; break;
#		case eControllerType::CALEON_RC50   :  m_inChCount =  2; m_outChCount =  2; break;
#		case eControllerType::EXT_CONTROLLER:  m_inChCount = 32; m_outChCount = 32; break;
#		case eControllerType::CALEONBOX     :  m_inChCount = 10; m_outChCount = 14; break;
#		default: break;
#	}
	def getInputNumber(self):
		if self.getType() == 'SWK_1':
			return 6
		return 10
	
	def getOutputNumber(self):
		if self.getType() == 'SWK_1':
			return 8
		return 10
	
	
	def setOutputMapping(self, channelId, mapping):
		self._output[channelId].setMapping(mapping)
	
	def setOutputValue(self, channelId, value):
		self._output[channelId].setValue(value)
	
	def getOutputMapping(self, channelId):
		return self._output[channelId].getMapping()
	
	def getOutputValue(self, channelId):
		return self._output[channelId].getValue()
	
	def reportOutputMapping(self, channelId):
		mapping = self.getOutputMapping(channelId)
		reportOutputMapping(self.getId(), channelId, mapping)
		
	def reportChannelNumber(self):
		msg = smartnetMessage(
		snc.ProgramType['CONTROLLER'],
		self.getId(),
		snc.ControllerFunction['GET_CHANNEL_NUMBER'],
		snc.requestFlag['RESPONSE'],
		[self.getInputNumber(), self.getOutputNumber()])
		msg.send()
		
	def on_message_received(self, message):
		if message is None:
			return

		msg = smartnetMessage()
		msg.parse(message)

		if msg is None:
			return
		
		def controllerOutputMappingRequestFilter():
			headerOk = ((msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
					(msg.getFunctionId () == snc.ControllerFunction['GET_RELAY_MAPPING']) and
					(msg.getRequestFlag() == snc.requestFlag['REQUEST']) and
					(msg.getProgramId() == self.getId()))

			return headerOk

		def controllerChannelNumberRequestFilter():
			headerOk = ((msg.getProgramType() == snc.ProgramType['CONTROLLER']) and
					(msg.getFunctionId () == snc.ControllerFunction['GET_CHANNEL_NUMBER']) and
					(msg.getRequestFlag() == snc.requestFlag['REQUEST']) and
					(msg.getProgramId() == self.getId()))

			return headerOk

		if controllerOutputMappingRequestFilter():
			data        = msg.getData()
			outputId    = data[0]
			self.reportOutputMapping(outputId)
			return
			
		if controllerChannelNumberRequestFilter():
			self.reportChannelNumber()
			
			
	def run(self):
		dT = time.time() - self._time_start
		if dT > 10:
			self._time_start = time.time()
			sendImHere(self.getId(), self.getType())
