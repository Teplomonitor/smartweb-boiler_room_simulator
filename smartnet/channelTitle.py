'''
@author: admin
'''

InputTitleOat = [
	'Улица',
]
InputTitleCascade           = [
	'Коллектор',
	'Внешний запрос',
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
	'Т воды',
	'Внешний запрос',
	'Уровень воды',
	'Проток',
	]
InputTitleSnowMelt          = [
	'Т подачи',
	'Т обратки',
	'Т поверхности',
	'Осадки',
	]
InputTitleBoiler            = [
	'Т котла',
	'Т обратки',
	'Внешний запрос',
	'Ошибка котла',
	]
InputTitleSolarCollector    = [
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	]
InputTitleGenericRelay = [
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	]
InputTitleAlarm        = [
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	]
InputTitleFillingLoop  = [
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
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
	'Вентиляция',
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
	'Цирк. насос',
	'Насос загрузки',
	'Контроль уровня воды',
	]
OutputTitleSnowMelt          = [
	'Насос загрузки',
	'Цирк. насос',
	'А. насос загрузки',
	]
OutputTitleBoiler         = [
	'Насос',
	'Ступень 1',
	'Ступень 2',
	'Мощность',
	'Температура',
	'Контроль обратки',
	]
OutputTitleSolarCollector = [
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	'СК',
	]
OutputTitleGenericRelay   = [
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	'Реле',
	]
OutputTitleAlarm          = [
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	'Сигнал',
	]
OutputTitleFillingLoop    = [
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	'Улица',
	]


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
	'GENERIC_RELAY'    : InputTitleGenericRelay     ,
	'ALARM'            : InputTitleAlarm            ,
	'FILLING_LOOP'     : InputTitleFillingLoop      ,
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
	'GENERIC_RELAY'    : OutputTitleGenericRelay     ,
	'ALARM'            : OutputTitleAlarm            ,
	'FILLING_LOOP'     : OutputTitleFillingLoop      ,
}

