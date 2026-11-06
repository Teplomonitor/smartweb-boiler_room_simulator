"""Ventilation I/O indexes match SmartWeb's DataProgramVentilation."""

from .program import Program, input_info, output_info
from gui.parameter import GuiParameter
import smartnet.constants as snc


class Ventilation(Program):
	@staticmethod
	def get_type():
		return snc.ProgramType.VENTILATION

	def init_inputs(self):
		self._inputs.update({
			'filter': input_info(0, 'Датчик фильтра'),
			'return_temperature': input_info(1, 'Обратка калорифера', -40, 120),
			'air_temperature': input_info(2, 'Воздух в канале', -40, 120),
			'fire_alarm': input_info(3, 'Пожарная тревога'),
		})

	def init_outputs(self):
		self._outputs.update({
			'supply_fan': output_info(0, 'Приточный вентилятор'),
			'exhaust_fan': output_info(1, 'Вытяжной вентилятор'),
			'outer_shutter': output_info(2, 'Наружные заслонки'),
			'mixer_shutter': output_info(3, 'Смесительная заслонка'),
			'discrete_outer_shutter': output_info(4, 'Наружные заслонки (реле)'),
			'discrete_mixer_shutter': output_info(5, 'Смесительная заслонка (реле)'),
			'fan_enable': output_info(6, 'Вентиляторы (реле)'),
			'heater': output_info(7, 'Электронагреватель'),
			'alarm': output_info(8, 'Сигнализация фильтра'),
		})

	def init_gui_parameters(self):
		self._parameters.update({
			'air_flow': GuiParameter(300, 'Макс. расход воздуха', 0, 3000, 10, 'м³/ч'),
			'electric_power': GuiParameter(2, 'Мощность электронагревателя', 0, 30, 0.1, 'кВт'),
			'coil_conductance': GuiParameter(200, 'Теплопередача калорифера', 0, 3000, 10, 'Вт/К'),
			'coil_capacity': GuiParameter(40, 'Теплоёмкость калорифера', 1, 1000, 1, 'кДж/К'),
			'duct_capacity': GuiParameter(5, 'Теплоёмкость канала', 1, 100, 1, 'кДж/К'),
			'outdoor_humidity': GuiParameter(15, 'Влажность наружного воздуха (модель)', 0, 100, 1, '%'),
		})

	def is_supply_exhaust(self):
		scheme = self.get_scheme()
		if isinstance(scheme, str):
			scheme = snc.ProgramScheme.get(scheme)
		if scheme not in (0, 1):
			raise ValueError(f'Unsupported ventilation scheme: {self.get_scheme()}')
		return scheme == 1