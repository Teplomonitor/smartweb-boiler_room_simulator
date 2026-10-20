"""Metadata for BOILER parameters, excluding channel pseudo-parameters."""

from smartnet.constants import TemperatureGeneratorParameterId
from .common import SCHEDULE_ARRAY_SIZE

PARAMETER_INFO = {
	TemperatureGeneratorParameterId.MAXIMUM_TEMPERATURE: {'type': 'TEMPERATURE'},
	TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE: {'type': 'TEMPERATURE'},
	TemperatureGeneratorParameterId.MINIMUM_TEMPERATURE_RESTRICTION: {'type': 'UINT8_T'},
	TemperatureGeneratorParameterId.ABSOLUTE_HYSTERESIS: {'type': 'TEMPERATURE'},
	TemperatureGeneratorParameterId.HYSTERESIS_REDUCE_TIME: {'type': 'TIME_MS'},
	TemperatureGeneratorParameterId.SECOND_STAGE_ON_DELAY: {'type': 'TIME_MS'},
	TemperatureGeneratorParameterId.SECOND_STAGE_HYSTERESIS: {'type': 'TEMPERATURE'},
	TemperatureGeneratorParameterId.PUMP_OFF_DELAY: {'type': 'TIME_MS'},
	TemperatureGeneratorParameterId.STAGE_1_POWER: {'type': 'UINT8_T'},
	TemperatureGeneratorParameterId.STAGE_2_POWER: {'type': 'UINT8_T'},
	TemperatureGeneratorParameterId.MIN_ON_TIME: {'type': 'TIME_MS'},
	TemperatureGeneratorParameterId.MIN_OFF_TIME: {'type': 'TIME_MS'},
	TemperatureGeneratorParameterId.SCHEDULE: {
		'type': 'SCHEDULE',
		'array_size': SCHEDULE_ARRAY_SIZE,
	},
}