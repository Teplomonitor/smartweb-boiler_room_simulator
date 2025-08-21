'''
@author: admin
'''

import time
import csv
import os

logsRootDir = os.path.join(os.getcwd(), 'log')

class TimestampValue(object):
	def __init__(self, value):
		self._timestamp = time.time()
		self._value = value
	def getTimestamp(self):
		return self._timestamp
	def getValue(self):
		return self._value
	

class ParameterLog(object):
	def __init__(self, parameterType = None, parameterTitle = None):
		self._parameterType  = parameterType
		self._parameterTitle = parameterTitle
		self._timestampValueList = []
		self._saveType = 'ON_CHANGE'
		
	def setType (self, parameterType ): self._parameterType  = parameterType
	def setTitle(self, parameterTitle): self._parameterTitle = parameterTitle
	def setSaveType(self, saveType   ): self._saveType       = saveType
	def getTimestamp(self, index):
		#return self._valueLog[index].getTimestamp()
		return self._timestampValueList[index][0]
	
	def getValue(self, index):
		#return self._valueLog[index].getTimestamp()
		return self._timestampValueList[index][1]
	
	def doAppend(self, value         ):
#		self._valueLog.append(TimestampValue(value))
		self._timestampValueList.append([int(time.time()), round(value, 1)])
	
	def append(self, value):
		if len(self._timestampValueList) == 0:
			self.doAppend(value)
			return
		
		lastTimestamp = self.getTimestamp(-1)
		
		now = time.time()
		
		dt  = now - lastTimestamp
		# don't save too often
		if dt < 1:
			return
		
		lastValue     = self.getValue(-1)
		dv  = abs(value - lastValue)
		
		if self._saveType == 'ALWAYS':
			if (dv == 0) and dt < 3:
				return
			self.doAppend(value)
		elif self._saveType == 'ON_CHANGE':
			if dv != 0 or dt > 60:
				self.doAppend(value)
		elif self._saveType == 'TEMPERATURE':
			if (dv > 1) or dt > 10:
				self.doAppend(value)
	
	def saveToCsv(self, logDir):
		
		fullLogDir = os.path.join(logsRootDir, logDir)
		
		fields = ['time', self._parameterType]
		
		if not os.path.exists(fullLogDir):
			try:
				os.makedirs(fullLogDir)
			except OSError as e:
				print('Error %d: Can\'t create folder for log at "%s"' %(e.errno, fullLogDir))
				print('\r\n\n')
				return 1
		
		logPath = os.path.join(fullLogDir, self._parameterTitle + '.csv')
		
		with open(logPath, 'w', encoding='utf-8', newline='') as f:
			# using csv.writer method from CSV package
			write = csv.writer(f)
			write.writerow(fields)
			write.writerows(self._timestampValueList)
			pass
		
class ProgramLog(object):
	def __init__(self, program):
		self._program = program

class DataLogger(object):
	def __init__(self, programList):
		self._programList = programList
		
		self._log = []
		
		for prg in self._programList:
			self._log.append(ProgramLog(prg))
			pass
		
	def run(self):
		for prg in self._log:
			pass
