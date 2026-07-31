"""Metadata for VIRTUAL_CONTROLLER parameters."""

from smartnet.constants import VirtualControllerParameterId

PARAMETER_INFO = {
	VirtualControllerParameterId.CONTROLLERID: {'type': 'UINT8_T'},
	**{
		parameter_id: {'type': 'TEMPERATURE'}
		for parameter_id in VirtualControllerParameterId
		if parameter_id is not VirtualControllerParameterId.CONTROLLERID
	},
}
