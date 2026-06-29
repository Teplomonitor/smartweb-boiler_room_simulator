from scenario.scenario import Scenario as Parent


class SnowmelterScenario(Parent):
    def __init__(self, controllerHost, sim):
        super().__init__(controllerHost, sim)

        self._snowmelter = self._programList["snowmelter"]
        # some scenarios may not include an outdoor sensor in the programs
        self._outdoor = self._programList.get("oat")

    def get_required_programs(self):
        requiredProgramTypesList = {
            "snowmelter": "SNOWMELT",
            "oat": "OUTDOOR_SENSOR",
        }
        return requiredProgramTypesList

    def get_default_preset(self):
        return "snowmelter"

    def readFrostProtectionTemperatureValue(self):
        return self._snowmelter.read_parameter_value("frostProtectionTemp")

    def readRequiredPlateTemperatureValue(self):
        return self._snowmelter.read_parameter_value("reqPlateTemp")

    def readMinOutdoorTemperature(self):
        return self._snowmelter.read_parameter_value("minOutdoorTemp")

    def readMaxOutdoorTemperature(self):
        return self._snowmelter.read_parameter_value("maxOutdoorTemp")

    def readSnowmelterOutdoorTemperature(self):
        return self._snowmelter.read_parameter_value("outdoorTemp")

    def readRequiredFlowTemperature(self):
        return self._snowmelter.read_parameter_value("reqFlowTemp")

    def getCirculationPumpState(self):
        return self._snowmelter.getSecondaryPumpState().get_value()

    def circulationPumpIsOn(self):
        return self.getCirculationPumpState() != self.RELAY_OFF

    def circulationPumpIsOff(self):
        return self.getCirculationPumpState() == self.RELAY_OFF

    def getLoadingPumpState(self):
        return self._snowmelter.getPrimaryPumpState().get_value()

    def loadingPumpIsOn(self):
        return self.getLoadingPumpState() != self.RELAY_OFF

    def loadingPumpIsOff(self):
        return not self.loadingPumpIsOn()

    def pumpsAreOff(self):
        return self.loadingPumpIsOff() and self.circulationPumpIsOff()

    def getDirectFlowTemperature(self):
        return self._snowmelter.getDirectFlowTemperature().get_value()

    def setBacwardFlowTemperature(self, value):
        t = self._snowmelter.getBackwardFlowTemperature()
        self.set_sensor_value(t, value)

    def setPlateTemperature(self, value):
        t = self._snowmelter.getPlateTemperature()
        self.set_sensor_value(t, value)

    def setOutdoorTemperature(self, value):
        if self._outdoor is None:
            return
        t = self._outdoor.getOutdoorTemperature()
        self.set_sensor_value(t, value)

    def setMediumOutdoorTemperature(self):
        minTemp = self.readMinOutdoorTemperature()
        maxTemp = self.readMaxOutdoorTemperature()

        if (minTemp is None) or (maxTemp is None):
            return False

        midTemp = (minTemp + maxTemp) / 2
        self.setOutdoorTemperature(midTemp)
        return True
