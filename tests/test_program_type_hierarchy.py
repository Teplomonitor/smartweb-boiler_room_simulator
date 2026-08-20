import unittest

import smartnet.parameter_registry as parameter_registry
from smartnet.constants import ProgramParameterId, ProgramType, TemperatureSourceParameterId
from smartnet.program_type_hierarchy import get_parent_type, get_program_type_chain


class TestProgramTypeHierarchy(unittest.TestCase):
	def test_district_heating_chain(self):
		self.assertEqual(
			get_program_type_chain(ProgramType.DISTRICT_HEATING),
			[
				ProgramType.DISTRICT_HEATING,
				ProgramType.TEMPERATURE_SOURCE,
				ProgramType.PROGRAM,
			],
		)

	def test_unknown_type_has_no_parent(self):
		self.assertIsNone(get_parent_type(999))
		self.assertEqual(get_program_type_chain(999), [999])

	def test_inherited_parameter_reports_its_owner(self):
		parameter = parameter_registry.get_parameter(
			ProgramType.DISTRICT_HEATING,
			ProgramParameterId.ID,
		)
		self.assertIsNotNone(parameter)
		self.assertEqual(parameter.id, ProgramParameterId.ID)
		self.assertEqual(parameter.program_type, ProgramType.PROGRAM)
		self.assertEqual(
			parameter_registry.get_parameter_owner(
				ProgramType.DISTRICT_HEATING,
				ProgramParameterId.ID,
			),
			ProgramType.PROGRAM,
		)

	def test_local_parameter_precedes_parent_chain(self):
		parameter = parameter_registry.get_parameter(
			ProgramType.DISTRICT_HEATING,
			1,
		)
		self.assertIsNotNone(parameter)
		self.assertEqual(parameter.program_type, ProgramType.DISTRICT_HEATING)

	def test_direct_parent_parameter_lookup_is_unchanged(self):
		parameter = parameter_registry.get_parameter(
			ProgramType.TEMPERATURE_SOURCE,
			TemperatureSourceParameterId.ALARM_PROGRAM_ID,
		)
		self.assertIsNotNone(parameter)
		self.assertEqual(parameter.program_type, ProgramType.TEMPERATURE_SOURCE)


if __name__ == '__main__':
	unittest.main()
