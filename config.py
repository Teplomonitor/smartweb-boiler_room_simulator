'''
Created on 9 июл. 2025 г.

@author: admin
'''

import os

try:
	import configparser
except ImportError:
	import ConfigParser as configparser


class ConfigParserInstance():
	def __new__(cls, *args, **kwargs):
		if not hasattr(cls, 'instance'):
			cls.instance = super(ConfigParserInstance, cls).__new__(cls)
		return cls.instance
	
	def __init__(self):
		if hasattr(self, '_initDone'):
			return
		
		self._configParserInstance = configparser.ConfigParser()
	
		file_dir = os.path.dirname(__file__)
		self._settingsPath = os.path.join(file_dir, 'settings.ini')
		
		if not os.path.exists(self._settingsPath):
			self.createConfig(self._settingsPath)
	
		self._initDone = True
		
		
		
	def createConfig(self, path):
		"""
		Create default config file
		"""
		
		if os.name == "nt":
			default_preset   = 'district_heating'
		else:
			default_preset   = 'district_heating'
			
#		default_gui_enable     = True
#		default_can_udp_enable = True
#		default_can_udp_port   = 31987
		
	
		self._configParserInstance.set('DEFAULT', 'preset'        , default_preset        )
#		self._configParserInstance.set('DEFAULT', 'gui_enable'    , default_gui_enable    )
#		self._configParserInstance.set('DEFAULT', 'can_udp_enable', default_can_udp_enable)
#		self._configParserInstance.set('DEFAULT', 'can_udp_port'  , default_can_udp_port  )

		profiles_array = ['main',]
		
		for p in profiles_array:
			self._configParserInstance.add_section(p)
		
		with open(path, "w", encoding='utf-8') as config_file:
			self._configParserInstance.write(config_file)
	
		return self._configParserInstance
	
	def checkSection(self, profile):
		if not self._configParserInstance.has_section(profile):
			self._configParserInstance.add_section(profile)
			with open(self._settingsPath, "w", encoding='utf-8') as config_file:
				self._configParserInstance.write(config_file)
				
	def getParameterValue(self, profile, parameter):
		self._configParserInstance.read(self._settingsPath, encoding='utf-8')
	
		self.checkSection(profile)
		
		return self._configParserInstance.get(profile, parameter)
	
	def setParameterValue(self, profile, parameter, value):
		self._configParserInstance.read(self._settingsPath, encoding='utf-8')
		
		self.checkSection(profile)
		
		self._configParserInstance.set(profile, parameter, value)
		
		with open(self._settingsPath, "w", encoding='utf-8') as config_file:
			self._configParserInstance.write(config_file)
