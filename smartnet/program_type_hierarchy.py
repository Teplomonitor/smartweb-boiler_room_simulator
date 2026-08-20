"""Parent relationships between SmartWeb program types.

The relationships mirror SmartWeb's ``ProgramParentTypes`` table.  They are
used for protocol parameter metadata only; program inputs, outputs, and GUI
parameters remain defined by concrete simulator models.
"""

from typing import Dict, List, Optional, Union

from smartnet.constants import ProgramType


ProgramTypeValue = Union[ProgramType, int]


PROGRAM_TYPE_PARENTS: Dict[ProgramType, Optional[ProgramType]] = {
	ProgramType.CAN_PROGRAM_TYPE_UNDEFINED: None,
	ProgramType.PROGRAM: None,
	ProgramType.OUTDOOR_SENSOR: ProgramType.PROGRAM,
	ProgramType.CONSUMER: ProgramType.PROGRAM,
	ProgramType.CASCADE_MANAGER: ProgramType.TEMPERATURE_SOURCE,
	ProgramType.ROOM_DEVICE: ProgramType.PROGRAM,
	ProgramType.TEMPERATURE_SOURCE: ProgramType.PROGRAM,
	ProgramType.HEAT_ACCUMULATOR: ProgramType.PROGRAM,
	ProgramType.EXTENDED_CONTROLLER: ProgramType.PROGRAM,
	ProgramType.EXTENSION_CONTROLLER: ProgramType.PROGRAM,
	ProgramType.MONITORING_DEVICE: ProgramType.PROGRAM,
	ProgramType.CONTROLLER: ProgramType.PROGRAM,
	ProgramType.CIRCUIT: ProgramType.CONSUMER,
	ProgramType.SCHEDULE: ProgramType.PROGRAM,
	ProgramType.HEATING_CIRCUIT: ProgramType.CIRCUIT,
	ProgramType.DISTRICT_HEATING: ProgramType.TEMPERATURE_SOURCE,
	ProgramType.DHW: ProgramType.CONSUMER,
	ProgramType.FLOW_THROUGH_DHW: ProgramType.DHW,
	ProgramType.TEMPERATURE_GENERATOR: ProgramType.TEMPERATURE_SOURCE,
	ProgramType.POOL: ProgramType.CONSUMER,
	ProgramType.THERMOSTAT: ProgramType.PROGRAM,
	ProgramType.SNOWMELT: ProgramType.CONSUMER,
	ProgramType.REMOTE_CONTROL: ProgramType.PROGRAM,
	ProgramType.BOILER: ProgramType.TEMPERATURE_GENERATOR,
	ProgramType.CHILLER: ProgramType.TEMPERATURE_GENERATOR,
	ProgramType.SOLAR_COLLECTOR: ProgramType.PROGRAM,
	ProgramType.VENTILATION: ProgramType.PROGRAM,
	ProgramType.GENERIC_RELAY: ProgramType.PROGRAM,
	ProgramType.ALARM: ProgramType.PROGRAM,
	ProgramType.FILLING_LOOP: ProgramType.PROGRAM,
	ProgramType.VIRTUAL_CONTROLLER: ProgramType.PROGRAM,
	ProgramType.DOUBLE_PUMP: ProgramType.PROGRAM,
	ProgramType.LIN_CONTROLLER: ProgramType.PROGRAM,
	ProgramType.LIN_PUMP: ProgramType.LIN_CONTROLLER,
	ProgramType.OPEN_THERM_BOILER: ProgramType.TEMPERATURE_SOURCE,
	ProgramType.MODBUS_TEMPERATURE_SOURCE: ProgramType.TEMPERATURE_SOURCE,
	ProgramType.MB_OT_ADAPTER: ProgramType.MODBUS_TEMPERATURE_SOURCE,
	ProgramType.MODBUS_SENSOR: ProgramType.PROGRAM,
	ProgramType.NAVIEN_CASCADE_MANAGER: ProgramType.MODBUS_TEMPERATURE_SOURCE,
	ProgramType.NAVIEN_NFB: ProgramType.MODBUS_TEMPERATURE_SOURCE,
	ProgramType.WAREHOUSE_AREA: ProgramType.PROGRAM,
	ProgramType.TPT_VALVE_ADAPTER: ProgramType.PROGRAM,
	ProgramType.MODBUS_ADAPTER: ProgramType.TEMPERATURE_SOURCE,
}


def get_parent_type(program_type: ProgramTypeValue) -> Optional[ProgramType]:
	"""Return the immediate parent of ``program_type`` or ``None``."""
	try:
		program_type = ProgramType(program_type)
	except (TypeError, ValueError):
		return None
	return PROGRAM_TYPE_PARENTS.get(program_type)


def get_program_type_chain(program_type: ProgramTypeValue) -> List[ProgramType]:
	"""Return ``program_type`` followed by its ancestors, nearest first.

	Unknown values are returned as a one-item chain so callers can still inspect
	the requested type.  A visited set prevents malformed future mappings from
	causing an infinite loop.
	"""
	try:
		current = ProgramType(program_type)
	except (TypeError, ValueError):
		return [program_type]

	chain = []
	visited = set()
	while current is not None and current not in visited:
		chain.append(current)
		visited.add(current)
		current = PROGRAM_TYPE_PARENTS.get(current)
	return chain
