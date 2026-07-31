"""Central registry for program-parameter metadata.

Each program type owns its metadata module.  This package-level registry is the
stable interface consumed by the parameter registry and remote-control code.
"""

from smartnet.constants import ProgramType
from .cascade_manager import PARAMETER_INFO as CASCADE_MANAGER_PARAMETER_INFO
from .circuit import PARAMETER_INFO as CIRCUIT_PARAMETER_INFO
from .common import CASCADE_SOURCES_MAX_NUM, SCHEDULE_ARRAY_SIZE
from .consumer import PARAMETER_INFO as CONSUMER_PARAMETER_INFO
from .controller import PARAMETER_INFO as CONTROLLER_PARAMETER_INFO
from .district_heating import PARAMETER_INFO as DISTRICT_HEATING_PARAMETER_INFO
from .boiler import PARAMETER_INFO as BOILER_PARAMETER_INFO
from .dhw import PARAMETER_INFO as DHW_PARAMETER_INFO
from .heating_circuit import PARAMETER_INFO as HEATING_CIRCUIT_PARAMETER_INFO
from .outdoor_sensor import PARAMETER_INFO as OUTDOOR_SENSOR_PARAMETER_INFO
from .pool import PARAMETER_INFO as SWIMMING_POOL_PARAMETER_INFO
from .program import PARAMETER_INFO as PROGRAM_PARAMETER_INFO
from .room_device import PARAMETER_INFO as ROOM_DEVICE_PARAMETER_INFO
from .snowmelt import PARAMETER_INFO as SNOWMELTER_PARAMETER_INFO
from .temperature_source import PARAMETER_INFO as TEMPERATURE_SOURCE_PARAMETER_INFO
from .thermostat import PARAMETER_INFO as THERMOSTAT_PARAMETER_INFO
from .virtual_controller import PARAMETER_INFO as VIRTUAL_CONTROLLER_PARAMETER_INFO

ParameterDict = {
	ProgramType.PROGRAM:            PROGRAM_PARAMETER_INFO,
	ProgramType.BOILER:             BOILER_PARAMETER_INFO,
	ProgramType.DHW:                DHW_PARAMETER_INFO,
	ProgramType.ROOM_DEVICE:        ROOM_DEVICE_PARAMETER_INFO,
	ProgramType.CONTROLLER:         CONTROLLER_PARAMETER_INFO,
	ProgramType.HEATING_CIRCUIT:    HEATING_CIRCUIT_PARAMETER_INFO,
	ProgramType.CONSUMER:           CONSUMER_PARAMETER_INFO,
	ProgramType.CASCADE_MANAGER:    CASCADE_MANAGER_PARAMETER_INFO,
	ProgramType.DISTRICT_HEATING:   DISTRICT_HEATING_PARAMETER_INFO,
	ProgramType.SNOWMELT:           SNOWMELTER_PARAMETER_INFO,
	ProgramType.CIRCUIT:            CIRCUIT_PARAMETER_INFO,
	ProgramType.POOL:               SWIMMING_POOL_PARAMETER_INFO,
	ProgramType.OUTDOOR_SENSOR:     OUTDOOR_SENSOR_PARAMETER_INFO,
	ProgramType.TEMPERATURE_SOURCE: TEMPERATURE_SOURCE_PARAMETER_INFO,
	ProgramType.THERMOSTAT:         THERMOSTAT_PARAMETER_INFO,
	ProgramType.VIRTUAL_CONTROLLER: VIRTUAL_CONTROLLER_PARAMETER_INFO,
}
