preset.py


class ProgramPreset(object):
	'''
	classdocs
	'''
	
	def __init__(self,
			programType, programScheme, programId,
			programTitle, programSettings, programInputs, programOutputs):
		self._type      = programType
		self._scheme    = programScheme
		self._id        = programId
		self._title     = programTitle
		self._settings  = programSettings
		self._inputs    = programInputs
		self._outputs   = programOutputs


def getPresetsList() :
	return [
		ProgramPreset(enumProgramTypes::HEATING_CIRCUIT_PROGRAM, heatingCircuit::SCHEME_MIXED  , heatingCircuit1::getId, LANG(langHntPreset1Circuit1Title ), &heatingCircuit1::settings, heatingCircuit1::inputs, heatingCircuit1::outputs),
		ProgramPreset(enumProgramTypes::HEATING_CIRCUIT_PROGRAM, heatingCircuit::SCHEME_DIRECT , heatingCircuit2::getId, LANG(langHntPreset1DirectCircuit1), &heatingCircuit2::settings, None                   , heatingCircuit2::outputs),
		ProgramPreset(enumProgramTypes::ROOM_DEVICE_PROGRAM    , 0                             , room ::getId          , LANG(langHntPreset1Room1         ), &room ::settings          , room ::inputs          , None                    ),
		ProgramPreset(enumProgramTypes::ROOM_DEVICE_PROGRAM    , 0                             , roomD::getId          , LANG(langHntPreset1RoomDirect1   ), &roomD::settings          , roomD::inputs          , None                    ),
		ProgramPreset(enumProgramTypes::DHW_PROGRAM            , 0                             , DHW::getId            , None                              , &DHW::settings            , DHW::inputs            , DHW::outputs            ),
		ProgramPreset(enumProgramTypes::BOILER_PROGRAM         , 0                             , boiler::getId         , LANG(langHntPreset1Boiler1       ), None                      , None                   , boiler::outputs         ),
		ProgramPreset(enumProgramTypes::CASCADE_MANAGER_PROGRAM, 0                             , cascade::getId        , LANG(langHntPreset1Cascade       ), &cascade::settings        , cascade::inputs        , None                    ),
		ProgramPreset(enumProgramTypes::OUTDOOR_SENSOR_PROGRAM , 0                             , oat::getId            , LANG(langHntPreset1Oat           ), None                      , oat::inputs            , None                    ),
	]

