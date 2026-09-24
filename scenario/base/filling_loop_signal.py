"""Helpers for configuring the FILLING_LOOP pressure input."""


PRESSURE_INPUT_TYPE_OPENABLE = 0
PRESSURE_INPUT_TYPE_SHORTABLE = 1
PRESSURE_INPUT_TYPE_RANGEABLE = 2


def read_pressure_input_type(filling_loop):
	return filling_loop.read_parameter_value('pressureInputType')


def write_pressure_input_type(filling_loop, value):
	return filling_loop.write_parameter_value('pressureInputType', value) is not None
