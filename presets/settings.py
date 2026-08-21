
from smartnet.remoteControl import RemoteControlParameter as RemoteControlParameter
import smartnet.constants as snc

class DefaultSettings(object):
	def __init__(self,
				settings
			):
		self._settings = settings

	def get(self):
		return self._settings
	def getSource    (self): return  0
	def getSourceList(self): return [0]
	
class HeatingCircuitSettings(object):
	def __init__(self,
			source         = None,
			heatingSlope   = None,
			heatCalculationMode = None,
			requiredConstantFlowTemperature = None,
			temperatureCompensation = None,
			):
		self._source         = source
		self._heatingSlope   = heatingSlope
		self._heatCalculationMode = heatCalculationMode
		self._requiredConstantFlowTemperature = requiredConstantFlowTemperature
		self._temperatureCompensation = temperatureCompensation

	def get(self):
		settings = [
			RemoteControlParameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, self._source),
			RemoteControlParameter(snc.ProgramType.CIRCUIT , snc.CircuitParameterId.HEATING_SLOPE, self._heatingSlope),
		]
		if self._heatCalculationMode is not None:
			settings.append(RemoteControlParameter(
				snc.ProgramType.CIRCUIT,
				snc.CircuitParameterId.HEAT_CALCULATION_MODE,
				self._heatCalculationMode,
			))
		if self._requiredConstantFlowTemperature is not None:
			settings.append(RemoteControlParameter(
				snc.ProgramType.CIRCUIT,
				snc.CircuitParameterId.REQUIRED_CONSTANT_FLOW_TEMPERATURE,
				self._requiredConstantFlowTemperature,
			))
		if self._temperatureCompensation is not None:
			settings.append(RemoteControlParameter(
				snc.ProgramType.CONSUMER,
				snc.ConsumerParameterId.TEMPERATURE_COMPENSATION,
				self._temperatureCompensation,
			))
		return settings
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class DhwSettings(object):
	def __init__(self,
			source         = None,
			):
		self._source         = source

	def get(self):
		return [
			RemoteControlParameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, self._source),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class SnowMelterSettings(object):
	def __init__(self,
			source         = None,
			alarmProgram   = None
			):
		self._source         = source
		self._alarmProgram   = alarmProgram

	def get(self):
		return [
			RemoteControlParameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID    , self._source),
			RemoteControlParameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID, self._alarmProgram),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class CascadeSettings(object):
	def __init__(self,
			source_1 = None,
			source_2 = None,
			source_3 = None,
			source_4 = None,
			source_5 = None,
			source_6 = None,
			source_7 = None,
			source_8 = None,
			):

		self._sourceList = [
			source_1,
			source_2,
			source_3,
			source_4,
			source_5,
			source_6,
			source_7,
			source_8,
			]

	def get(self):
		result = []
		i = 0
		for source in self._sourceList:
			if source:
				result.append(
					RemoteControlParameter(snc.ProgramType.CASCADE_MANAGER, snc.CascadeManagerParameterId.PARAM_TEMPERATURE_SOURCE_ID, source, i)
				)
			i = i + 1

		return result

	def getSourceList(self):
		return self._sourceList


class RoomSettings(object):
	def __init__(self,
			source_1 = None,
			source_2 = None,
			source_3 = None,
			):

		self._sourceList = [
			source_1,
			source_2,
			source_3,
			]

	def get(self):
		return [
				RemoteControlParameter(snc.ProgramType.ROOM_DEVICE, snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_1, self._sourceList[0]),
				RemoteControlParameter(snc.ProgramType.ROOM_DEVICE, snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_2, self._sourceList[1]),
				RemoteControlParameter(snc.ProgramType.ROOM_DEVICE, snc.RoomDeviceParameterId.RESPONSIBLE_CIRCUIT_3, self._sourceList[2]),
			]
		
	def getSourceList(self):
		return self._sourceList
	

class DistrictHeatingSettings(object):
	def __init__(self,
			source         = None,
			alarm_program  = None,
			):
		self._source         = source
		self._alarm_program  = alarm_program

	def get(self):
		parameters = [
			RemoteControlParameter(snc.ProgramType.DISTRICT_HEATING, snc.DistrictHeatingParameterId.PARAM_TEMPERATURE_SOURCE_ID, self._source),
		]
		if self._alarm_program is not None:
			parameters.append(RemoteControlParameter(
				snc.ProgramType.TEMPERATURE_SOURCE,
				snc.TemperatureSourceParameterId.ALARM_PROGRAM_ID,
				self._alarm_program,
			))
		return parameters
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]

class SwimmingPoolSettings(object):
	def __init__(self,
			source         = None,
			alarmProgram   = None,
			):
		self._source         = source
		self._alarmProgram   = alarmProgram

	def get(self):
		return [
			RemoteControlParameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.GENERATOR_ID, self._source),
			RemoteControlParameter(snc.ProgramType.CONSUMER, snc.ConsumerParameterId.ALARM_PROGRAM_ID, self._alarmProgram),
		]
	def getSource    (self): return  self._source
	def getSourceList(self): return [self._source]
