'''
@author: admin
'''

InputTitleOat = [
	'Улица',
]
InputTitleCascade           = [
	'Коллектор',
	]
InputTitleRoomDevice        = [
	'Т помещения',
	'Режим',
	'Т пола',
	'Т стены',
	'Влажность',
	'CO2',
	'Движение',
	]
InputTitleHeatingCircuit    = [
	'Т подачи',
	'Термостат',
	'Внешний запрос',
	'Управление насосом',
	'Т обратки',
	]
InputTitleDistrictHeating   = [
	'Подача из города',
	'Обратка в город',
	'Подача в дом',
	'Обратка из дома',
	'Теплосчётчик',
	'Расход',
	'Внешний запрос',
	]
InputTitleDhw               = [
	'Т бойлера',
	'Проток',
	'Т обратки',
	]
InputTitlePool              = [
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	]
InputTitleSnowMelt          = [
	'Т подачи',
	'Т обратки',
	'Т поверхности',
	'Осадки',
	]
InputTitleBoiler            = [
	'Улица',
	]
InputTitleSolarCollector    = [
	'Улица',
	]
InputTitleSolarGenericRelay = [
	'Улица',
	]
InputTitleSolarAlarm        = [
	'Улица',
	]
InputTitleSolarFillingLoop  = [
	'Улица',
	]

OutputTitleOat               = []
OutputTitleCascade           = []
OutputTitleRoomDevice        = [
	'Клапан ТП',
	'Клапан РО',
	'Клапан ДН',
	'Сигнал ТП',
	'Сигнал РО',
	'Сигнал ДН',
	]
OutputTitleHeatingCircuit    = [
	'А.смеситель',
	'Смес. откр',
	'Смес. закр',
	'Насос',
	'Клапан',
	'Насос ТО',
	'А. насос',
	]
OutputTitleDistrictHeating   = [
	'Насос загрузки',
	'Цирк. насос',
	'Клапан',
	'А. клапан',
	]
OutputTitleDhw               = [
	'Насос загрузки',
	'Цирк. насос',
	'А. насос загрузки',
	'Смес. откр',
	'Смес. закр',
	]
OutputTitlePool              = [
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	'Бассейн',
	]
OutputTitleSnowMelt          = [
	'Насос загрузки',
	'Цирк. насос',
	'А. насос загрузки',
	]
OutputTitleBoiler            = ['Улица',]
OutputTitleSolarCollector    = ['Улица',]
OutputTitleSolarGenericRelay = ['Улица',]
OutputTitleSolarAlarm        = ['Улица',]
OutputTitleSolarFillingLoop  = ['Улица',]


ProgramInputTitle = {
	'OUTDOOR_SENSOR'   : InputTitleOat,
	'CASCADE_MANAGER'  : InputTitleCascade          ,
	'ROOM_DEVICE'      : InputTitleRoomDevice       ,
	'HEATING_CIRCUIT'  : InputTitleHeatingCircuit   ,
	'DISTRICT_HEATING' : InputTitleDistrictHeating  ,
	'DHW'              : InputTitleDhw              ,
	'POOL'             : InputTitlePool             ,
	'SNOWMELT'         : InputTitleSnowMelt         ,
	'BOILER'           : InputTitleBoiler           ,
	'SOLAR_COLLECTOR'  : InputTitleSolarCollector   ,
	'GENERIC_RELAY'    : InputTitleSolarGenericRelay,
	'ALARM'            : InputTitleSolarAlarm       ,
	'FILLING_LOOP'     : InputTitleSolarFillingLoop ,
}

ProgramOutputTitle = {
	'OUTDOOR_SENSOR'   : OutputTitleOat              ,
	'CASCADE_MANAGER'  : OutputTitleCascade          ,
	'ROOM_DEVICE'      : OutputTitleRoomDevice       ,
	'HEATING_CIRCUIT'  : OutputTitleHeatingCircuit   ,
	'DISTRICT_HEATING' : OutputTitleDistrictHeating  ,
	'DHW'              : OutputTitleDhw              ,
	'POOL'             : OutputTitlePool             ,
	'SNOWMELT'         : OutputTitleSnowMelt         ,
	'BOILER'           : OutputTitleBoiler           ,
	'SOLAR_COLLECTOR'  : OutputTitleSolarCollector   ,
	'GENERIC_RELAY'    : OutputTitleSolarGenericRelay,
	'ALARM'            : OutputTitleSolarAlarm       ,
	'FILLING_LOOP'     : OutputTitleSolarFillingLoop ,
}

