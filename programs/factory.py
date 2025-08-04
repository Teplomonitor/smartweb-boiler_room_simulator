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


def createProgram(preset):
	programType = preset.getType()
	
	programCreator = {
			'OUTDOOR_SENSOR'   : ProgramOat            ,
			'BOILER'           : ProgramBoiler         ,
			'CASCADE_MANAGER'  : ProgramCascade        ,
			'ROOM_DEVICE'      : ProgramRoom           ,
			'HEATING_CIRCUIT'  : ProgramHeatingCircuit ,
			'SNOWMELT'         : ProgramSnowmelter     ,
			'DHW'              : ProgramDhw            ,
			'DISTRICT_HEATING' : ProgramDistrictHeating,
			'FILLING_LOOP'     : ProgramFillingLoop    ,
			'TPT_VALVE_ADAPTER': ProgramTptValve       ,
			'POOL'             : ProgramSwimmingPool   ,
	}
	
	if programType in programCreator:
		prg = programCreator[programType](preset)
	else:
		consoleLog.printError(f'Wrong program type {programType}')
		prg = None
		
	return prg
		
		