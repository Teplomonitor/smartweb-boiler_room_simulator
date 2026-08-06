"""Metadata for CONTROLLER parameters."""

from smartnet.constants import ControllerParameterId

PARAMETER_INFO = {
	parameter_id: {'type': 0}
	for parameter_id in ControllerParameterId
}

PARAMETER_INFO[ControllerParameterId.DATE] = {'type': 'DATE'}
PARAMETER_INFO[ControllerParameterId.TIME] = {'type': 'TIME'}
