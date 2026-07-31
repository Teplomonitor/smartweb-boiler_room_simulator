"""
Parameter registry for accessing parameter metadata with caching.

Provides a centralized registry to look up parameter definitions by program type
and parameter ID. Implements caching to avoid repeated dictionary lookups.
"""

import logging
from typing import Optional, Dict, Tuple, Any

import smartnet.constants as snc

# Configure logger for this module
logger = logging.getLogger(__name__)


class ParameterDefinition:
	"""
	Immutable wrapper for parameter metadata.
	
	Encapsulates the properties of a parameter: id, type, and array_size.
	"""
	
	def __init__(self, metadata: Dict[str, Any]):
		"""
		Initialize parameter definition from metadata dictionary.
		
		Args:
			metadata: Dictionary with keys 'id', 'type', and optionally 'array_size'
		"""
		self._id = metadata.get('id')
		self._type = metadata.get('type')
		self._array_size = metadata.get('array_size', 1)
	
	@property
	def id(self) -> int:
		"""Get the parameter ID code."""
		return self._id
	
	@property
	def type(self):
		"""Get the parameter type (e.g., 'UINT8_T', 'TEMPERATURE', 'TIME_MS')."""
		return self._type
	
	@property
	def array_size(self) -> int:
		"""Get the array size. Defaults to 1 for scalar parameters."""
		return self._array_size
	
	def is_array(self) -> bool:
		"""Check if this parameter is an array type."""
		return self._array_size > 1
	
	def is_string(self) -> bool:
		"""Check if this parameter is a string type."""
		return self._type == 'STRING'


class ParameterRegistry:
	"""
	Singleton registry for parameter metadata with caching.
	
	Provides efficient lookups of parameter definitions indexed by
	(program_type, parameter_id) with memoization.
	"""
	
	_instance = None
	_cache: Dict[Tuple[int, str], Optional[ParameterDefinition]] = {}
	
	def __new__(cls):
		"""Ensure singleton pattern."""
		if cls._instance is None:
			cls._instance = super(ParameterRegistry, cls).__new__(cls)
		return cls._instance
	
	def get_parameter(
		self,
		program_type: int,
		parameter_id: int
	) -> Optional[ParameterDefinition]:
		"""
		Get parameter definition by program type and parameter ID.
		
		Caches results to avoid repeated dictionary lookups.
		
		Args:
			program_type: The program type (e.g., ProgramType.ROOM_DEVICE)
			parameter_id: The parameter ID code (int or IntEnum member)
		
		Returns:
			ParameterDefinition if found, None if not found (with warning log)
		"""
		# Convert IntEnum to int if needed
		if hasattr(parameter_id, 'value'):
			parameter_id = int(parameter_id)
		
		cache_key = (program_type, parameter_id)
		
		# Return cached result if available
		if cache_key in self._cache:
			return self._cache[cache_key]
		
		# Look up in ParameterDict
		if program_type not in snc.ParameterDict:
			logger.warning(
				f'Program type {program_type} not found in ParameterDict'
			)
			self._cache[cache_key] = None
			return None
		
		param_info_dict = snc.ParameterDict[program_type]
		
		if parameter_id not in param_info_dict:
			logger.warning(
				f'Parameter ID {parameter_id} not found for program type {program_type}'
			)
			self._cache[cache_key] = None
			return None
		
		# Create and cache the definition
		metadata = param_info_dict[parameter_id]
		param_def = ParameterDefinition(metadata)
		self._cache[cache_key] = param_def
		
		return param_def
	
	def is_string(self, program_type: int, parameter_id: str) -> bool:
		"""
		Check if parameter is a string type.
		
		Args:
			program_type: The program type
			parameter_id: The parameter ID string
		
		Returns:
			True if parameter type is 'STRING', False otherwise
		"""
		param_def = self.get_parameter(program_type, parameter_id)
		if param_def is None:
			return False
		return param_def.is_string()
	
	def is_array(self, program_type: int, parameter_id: str) -> bool:
		"""
		Check if parameter is an array type (array_size > 1).
		
		Args:
			program_type: The program type
			parameter_id: The parameter ID string
		
		Returns:
			True if parameter array_size > 1, False otherwise
		"""
		param_def = self.get_parameter(program_type, parameter_id)
		if param_def is None:
			return False
		return param_def.is_array()


# Singleton instance for module-level access
_registry_instance = ParameterRegistry()


def get_parameter(
	program_type: int,
	parameter_id: int
) -> Optional[ParameterDefinition]:
	"""
	Module-level convenience function to get parameter definition.
	
	Args:
		program_type: The program type
		parameter_id: The parameter ID code (int or IntEnum member)
	
	Returns:
		ParameterDefinition if found, None otherwise
	"""
	return _registry_instance.get_parameter(program_type, parameter_id)


def is_string(program_type: int, parameter_id: str) -> bool:
	"""
	Module-level convenience function to check if parameter is string.
	
	Args:
		program_type: The program type
		parameter_id: The parameter ID string
	
	Returns:
		True if parameter type is 'STRING'
	"""
	return _registry_instance.is_string(program_type, parameter_id)


def is_array(program_type: int, parameter_id: str) -> bool:
	"""
	Module-level convenience function to check if parameter is array.
	
	Args:
		program_type: The program type
		parameter_id: The parameter ID string
	
	Returns:
		True if parameter array_size > 1
	"""
	return _registry_instance.is_array(program_type, parameter_id)
