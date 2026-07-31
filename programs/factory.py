'''
@author: admin
'''

import consoleLog

from programs.boiler          import Boiler          as ProgramBoiler
from programs.heating_circuit import HeatingCircuit  as ProgramHeatingCircuit
from programs.room            import Room            as ProgramRoom
from programs.districtHeating import DistrictHeating as ProgramDistrictHeating
from programs.oat             import Oat             as ProgramOat
from programs.dhw             import Dhw             as ProgramDhw
from programs.snowmelter      import Snowmelter      as ProgramSnowmelter
from programs.cascade         import Cascade         as ProgramCascade
from programs.fillingLoop     import FillingLoop     as ProgramFillingLoop
from programs.tptValve        import TptValve        as ProgramTptValve
from programs.swimmingPool    import SwimmingPool    as ProgramSwimmingPool
from programs.virtualController import VirtualController as ProgramVirtualController

import smartnet.constants as snc

programCreator = {
		snc.ProgramType.OUTDOOR_SENSOR     : ProgramOat            ,
		snc.ProgramType.BOILER             : ProgramBoiler         ,
		snc.ProgramType.CASCADE_MANAGER    : ProgramCascade        ,
		snc.ProgramType.ROOM_DEVICE        : ProgramRoom           ,
		snc.ProgramType.HEATING_CIRCUIT    : ProgramHeatingCircuit ,
		snc.ProgramType.SNOWMELT           : ProgramSnowmelter     ,
		snc.ProgramType.DHW                : ProgramDhw            ,
		snc.ProgramType.DISTRICT_HEATING   : ProgramDistrictHeating,
		snc.ProgramType.FILLING_LOOP       : ProgramFillingLoop    ,
		snc.ProgramType.TPT_VALVE_ADAPTER  : ProgramTptValve       ,
		snc.ProgramType.POOL               : ProgramSwimmingPool   ,
		snc.ProgramType.VIRTUAL_CONTROLLER : ProgramVirtualController,
}

def createProgram(preset):
	programType = preset.get_type()
	
	if programType in programCreator:
		prg = programCreator[programType](preset)
	else:
		consoleLog.print_error(f'Wrong program type {programType}')
		prg = None
		
	return prg
		
		