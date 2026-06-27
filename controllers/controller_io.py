'''
Created on 9 апр. 2025 г.

@author: admin
'''

import time
import smartnet.message   as sm
import smartnet.channelMapping as scm
from functions.periodicTrigger import PeriodicTrigger as PeriodicTrigger
import smartnet.constants as snc

def reportOutputMapping(controllerId, outputId, mapping):
	if mapping is None: return False

	msg = sm.Message(
			snc.ProgramType['CONTROLLER'],
			controllerId,
			snc.ControllerFunction['GET_RELAY_MAPPING'],
			snc.requestFlag['RESPONSE'],
			[outputId, mapping.getRaw(0), mapping.getRaw(1)])
	
	msg.send()
	return True

def sendImHere(controllerId, controllerType):
	msg = sm.Message(
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
		self._reportImHereTrigger        = PeriodicTrigger()
		self._reportOutputMappingTrigger = PeriodicTrigger()
		
		self.can_subscribe()
		
		inputs_num  = self.getInputNumber ()
		outputs_num = self.getOutputNumber()
		
		self._inputs  = [scm.Channel(None, None) for _ in range(inputs_num )]
		self._outputs = [scm.Channel(None, None) for _ in range(outputs_num)]
		
		sendImHere(self.get_id(), self.get_type())
		self.reportChannelNumber()
	
	def clear(self):
		self.can_unsubscribe()
		self._inputs  = []
		self._outputs = []
		
	def can_subscribe(self):
		sm.CanListener.subscribe(self)
		
	def can_unsubscribe(self):
		sm.CanListener.unsubscribe(self)
		
	def __del__(self):
		print('kill ctrlIO')
		self.can_unsubscribe()
		
	def get_type     (self): return self._type
	def get_id       (self): return self._id
	def get_title    (self): return self._title
	
	
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
		if self.get_type() == 'SWK_1':
			return 6
		return 10
	
	def getOutputNumber(self):
		if self.get_type() == 'SWK_1':
			return 8
		return 10
	
	
	def setOutputMapping(self, channelId, mapping):
		self._outputs[channelId].setMapping(mapping)
	
	def set_output_value(self, channelId, value):
		self._outputs[channelId].setValue(value)
	
	def getOutputMapping(self, channelId):
		return self._outputs[channelId].getMapping()
	
	def getOutputValue(self, channelId):
		return self._outputs[channelId].getValue()
	
	def reportOutputMapping(self, channelId):
		mapping = self.getOutputMapping(channelId)
		reportOutputMapping(self.get_id(), channelId, mapping)
		
	def reportChannelNumber(self):
		msg = sm.Message(
		snc.ProgramType['CONTROLLER'],
		self.get_id(),
		snc.ControllerFunction['GET_CHANNEL_NUMBER'],
		snc.requestFlag['RESPONSE'],
		[self.getInputNumber(), self.getOutputNumber()])
		msg.send()
		
	def on_can_message_received(self, msg):
		if msg is None:
			return
		
		def controllerOutputMappingRequestFilter():
			headerOk = ((msg.get_program_type() == snc.ProgramType['CONTROLLER']) and
					(msg.getFunctionId () == snc.ControllerFunction['GET_RELAY_MAPPING']) and
					(msg.getRequestFlag() == snc.requestFlag['REQUEST']) and
					(msg.getProgramId() == self.get_id()))

			return headerOk

		def controllerChannelNumberRequestFilter():
			headerOk = ((msg.get_program_type() == snc.ProgramType['CONTROLLER']) and
					(msg.getFunctionId () == snc.ControllerFunction['GET_CHANNEL_NUMBER']) and
					(msg.getRequestFlag() == snc.requestFlag['REQUEST']) and
					(msg.getProgramId() == self.get_id()))

			return headerOk

		if controllerOutputMappingRequestFilter():
			data        = msg.get_data()
			outputId    = data[0]
			self.reportOutputMapping(outputId)
		elif controllerChannelNumberRequestFilter():
			self.reportChannelNumber()
			
		
	def run(self):
		if self._reportImHereTrigger.get(10):
			sendImHere(self.get_id(), self.get_type())
			
		if self._reportOutputMappingTrigger.get(5*60):
			num = self.getOutputNumber()
			for output_id in range (num):
				if self.getOutputMapping(output_id) and self.getOutputMapping(output_id).getChannelType() != 'CHANNEL_UNDEFINED':
					self.reportOutputMapping(output_id)
					time.sleep(0.1)
			

def initVirtualControllers(controllerIoList):
	ctrlIo = []
	if controllerIoList:
		for ctrl in controllerIoList:
			ctrlIo.append(ControllerIO(ctrl.get_id(), ctrl.get_type(), ctrl.get_title()))
	return ctrlIo
