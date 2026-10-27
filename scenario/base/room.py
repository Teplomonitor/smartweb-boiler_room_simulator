"""Shared setup and cleanup for room mode checklist scenarios."""

from datetime import datetime, timedelta
import math

from consoleLog import print_error, print_log
from scenario.scenario import Scenario as Parent
import smartnet.constants as snc
from smartnet.remoteControl import RemoteControlParameter
from smartnet.room import set_group_work_mode


class RoomCheckFailed(Exception):
	pass


class RoomScenario(Parent):
	TEST_SCHEDULE = False
	GROUP = 1
	OTHER_GROUP = 2
	COMFORT_TEMPERATURE = 23
	ECONOM_TEMPERATURE = 17
	OFF_TEMPERATURE = 8
	TEMPERATURE_TOLERANCE = 0.2
	MODE_TIMEOUT = 60
	STABLE_DURATION = 3
	SCHEDULE_LEAD_MINUTES = 4
	SCHEDULE_COMFORT_MINUTES = 2
	SCHEDULE_WRITE_MARGIN = 60
	SCHEDULE_TIMEOUT = 10 * 60
	CLOCK_READ_ATTEMPTS = 3

	def force_preset_load(self):
		return True

	def get_default_preset(self):
		return 'room'

	def get_required_programs(self):
		return {
			'room_1': snc.ProgramType.ROOM_DEVICE,
			'room_2': snc.ProgramType.ROOM_DEVICE,
			'room_3': snc.ProgramType.ROOM_DEVICE,
			'control_room': snc.ProgramType.ROOM_DEVICE,
		}

	def _parameter(self, room, parameter_id, value=None, index=None):
		return RemoteControlParameter(
			programType=snc.ProgramType.ROOM_DEVICE, parameterId=parameter_id,
			programId=room.get_id(), parameterValue=value, parameterIndex=index,
		)

	def _read(self, room, parameter_id, index=None):
		parameter = self._parameter(room, parameter_id, index=index)
		value = parameter.get_value() if parameter.read() else None
		if value is None:
			raise RoomCheckFailed(f'Комната {room.get_id()}: не прочитан параметр {parameter_id}/{index}')
		return value

	def _put(self, room, parameter_id, value, index=None):
		parameter = self._parameter(room, parameter_id, value, index)
		if not parameter.write():
			raise RoomCheckFailed(f'Комната {room.get_id()}: не записан параметр {parameter_id}/{index}')
		# Schedule writes have no acknowledgement (eight-byte CAN payload).
		if self._read(room, parameter_id, index) != value:
			raise RoomCheckFailed(f'Комната {room.get_id()}: не подтверждён параметр {parameter_id}/{index}')

	@staticmethod
	def _require(condition, message):
		if not condition:
			raise RoomCheckFailed(message)

	def _expect_modes(self, expected):
		last_modes = []

		def matches():
			nonlocal last_modes
			last_modes = [self._read(room, snc.RoomDeviceParameterId.WORK_MODE) for room in self._rooms]
			return last_modes == list(expected)

		self._require(self.wait_state_permanence(matches, self.STABLE_DURATION, self.MODE_TIMEOUT),
			f'Режимы комнат: ожидалось {list(expected)}, получено {last_modes}')

	def _expect_temperature(self, mode, temperature):
		room = self._rooms[0]
		last_value = None

		def matches():
			nonlocal last_value
			current_mode = self._read(room, snc.RoomDeviceParameterId.WORK_MODE)
			last_value = self._read(room, snc.RoomDeviceParameterId.ROOM_DESIRED_TEMPERATURE)
			return (current_mode == mode and isinstance(last_value, (int, float))
				and math.isfinite(last_value) and abs(last_value - temperature) <= self.TEMPERATURE_TOLERANCE)

		self._require(self.wait_state_permanence(matches, self.STABLE_DURATION, self.MODE_TIMEOUT),
			f'Режим {mode}: ожидалось {temperature} C, получено {last_value}')

	def _read_controller_clock(self):
		def read(parameter_id):
			parameter = RemoteControlParameter(
				programType=snc.ProgramType.CONTROLLER, parameterId=parameter_id,
				programId=self._controllerHost.get_controller_id(),
			)
			value = parameter.get_value() if parameter.read() else None
			self._require(value is not None, f'Не прочитаны часы контроллера: {parameter_id}')
			return value

		for _ in range(self.CLOCK_READ_ATTEMPTS):
			date = read(snc.ControllerParameterId.DATE)
			clock = read(snc.ControllerParameterId.TIME)
			if date != read(snc.ControllerParameterId.DATE):
				continue
			try:
				day, weekday, month, year = date
				hour, minute, second, _ = clock
				self._require(isinstance(weekday, int) and 0 <= weekday < 7,
					'Некорректный день недели контроллера')
				return datetime(year, month, day, hour, minute, second), weekday
			except (TypeError, ValueError) as error:
				raise RoomCheckFailed(f'Некорректные дата/время контроллера: {date}, {clock}') from error
		raise RoomCheckFailed('Не удалось согласованно прочитать дату и время контроллера')

	@classmethod
	def _schedule_window(cls, now, weekday):
		"""Split the future comfort window at midnight; use the controller's weekday."""
		start = now.replace(second=0, microsecond=0) + timedelta(minutes=cls.SCHEDULE_LEAD_MINUTES)
		end = start + timedelta(minutes=cls.SCHEDULE_COMFORT_MINUTES)
		table = {(day, period): (0, 0) for day in range(7) for period in range(3)}
		cursor = start
		while cursor < end:
			next_day = cursor.replace(hour=0, minute=0) + timedelta(days=1)
			stop = min(next_day, end)
			day = (weekday + (cursor.date() - now.date()).days) % 7
			end_minutes = 1440 if stop == next_day else stop.hour * 60 + stop.minute
			table[day, 0] = (cursor.hour * 60 + cursor.minute, end_minutes)
			cursor = stop
		return start, end, table

	def _wait_controller_time(self, target):
		self._require(self.wait_event(
			lambda: self._read_controller_clock()[0] >= target, self.SCHEDULE_TIMEOUT,
		), f'Часы контроллера не достигли {target}; возможна остановка или коррекция часов')

	def _check_schedule(self):
		room = self._rooms[0]
		now, weekday = self._read_controller_clock()
		start, end, table = self._schedule_window(now, weekday)
		print_log(f'Часы контроллера: {now}, день недели={weekday}; комфорт {start} — {end}')
		for index, value in table.items():
			self._put(room, snc.RoomDeviceParameterId.SCHEDULE, value, index)
		written_at, _ = self._read_controller_clock()
		self._require(now <= written_at < start - timedelta(seconds=self.SCHEDULE_WRITE_MARGIN),
			'Недостаточный запас времени после записи расписания или изменились часы контроллера')
		self._put(room, snc.RoomDeviceParameterId.WORK_MODE, snc.RoomWorkMode.PROGRAM)
		self._expect_temperature(snc.RoomWorkMode.PROGRAM, self.ECONOM_TEMPERATURE)
		self._wait_controller_time(start)
		self._expect_temperature(snc.RoomWorkMode.PROGRAM, self.COMFORT_TEMPERATURE)
		self._require(self._read_controller_clock()[0] < end,
			'Пропущен комфортный интервал расписания')
		self._wait_controller_time(end)
		self._expect_temperature(snc.RoomWorkMode.PROGRAM, self.ECONOM_TEMPERATURE)

	def _temperature_sequence(self):
		room = self._rooms[0]
		for mode, temperature in (
			(snc.RoomWorkMode.COMFORT, self.COMFORT_TEMPERATURE),
			(snc.RoomWorkMode.ECONOM, self.ECONOM_TEMPERATURE),
			(snc.RoomWorkMode.OFF, self.OFF_TEMPERATURE),
			(snc.RoomWorkMode.COMFORT, self.COMFORT_TEMPERATURE),
		):
			print_log(f'Комната: режим {mode.name}, требуемая температура {temperature} C')
			self._put(room, snc.RoomDeviceParameterId.WORK_MODE, mode)
			self._expect_temperature(mode, temperature)
		self._check_schedule()

	def _group_sequence(self, broadcast):
		for room, group in zip(self._rooms, (self.GROUP,) * 3 + (self.OTHER_GROUP,)):
			self._put(room, snc.RoomDeviceParameterId.GROUP, group)
		# The control room is OFF; every new target mode differs from the preceding one.
		for source in (self._rooms[:1] if broadcast else self._rooms[:3]):
			for mode in (snc.RoomWorkMode.COMFORT, snc.RoomWorkMode.ECONOM,
					snc.RoomWorkMode.PROGRAM, snc.RoomWorkMode.OFF):
				print_log(f'Группа {self.GROUP}: {mode.name}, источник={"CAN-группа" if broadcast else source.get_id()}')
				if broadcast:
					set_group_work_mode(self.GROUP, mode)
				else:
					self._put(source, snc.RoomDeviceParameterId.WORK_MODE, mode)
				self._expect_modes([mode] * 3 + [snc.RoomWorkMode.OFF])

	def _run_test(self, sequence):
		self._status = 'FAIL'
		self._rooms = [self._programList[key] for key in self.get_required_programs()]
		parameter = snc.RoomDeviceParameterId
		settings = [(room, parameter.WORK_MODE) for room in self._rooms]
		settings += [(self._rooms[0], item) for item in (
			parameter.ROOM_COMFORT_TEMPERATURE, parameter.ROOM_REDUCED_TEMPERATURE,
			parameter.ROOM_OFF_TEMPERATURE,
		)] if self.TEST_SCHEDULE else []
		try:
			saved_groups = [(room, self._read(room, parameter.GROUP)) for room in self._rooms]
			saved = [(room, item, self._read(room, item)) for room, item in settings]
			saved_schedule = [
				((day, period), self._read(self._rooms[0], parameter.SCHEDULE, (day, period)))
				for day in range(7) for period in range(3)
			] if self.TEST_SCHEDULE else []
		except RoomCheckFailed as error:
			print_error(str(error))
			return
		try:
			for room in self._rooms:
				self._put(room, parameter.GROUP, 0)
			for room in self._rooms:
				self._put(room, parameter.WORK_MODE, snc.RoomWorkMode.OFF)
			if self.TEST_SCHEDULE:
				for item, value in (
					(parameter.ROOM_COMFORT_TEMPERATURE, self.COMFORT_TEMPERATURE),
					(parameter.ROOM_REDUCED_TEMPERATURE, self.ECONOM_TEMPERATURE),
					(parameter.ROOM_OFF_TEMPERATURE, self.OFF_TEMPERATURE),
				):
					self._put(self._rooms[0], item, value)
			sequence()
			self._status = 'OK'
		except RoomCheckFailed as error:
			print_error(str(error))
		finally:
			def restore(room, item, value, index=None):
				try:
					self._put(room, item, value, index)
				except Exception as error:
					self._status = 'FAIL'
					print_error(f'Не восстановлен параметр комнаты {room.get_id()}, {item}/{index}: {error}')

			# Suppress mode propagation while restoring each room's individual state.
			for room in self._rooms:
				restore(room, parameter.GROUP, 0)
			for index, value in saved_schedule:
				restore(self._rooms[0], parameter.SCHEDULE, value, index)
			for room, item, value in reversed(saved):
				restore(room, item, value)
			for room, group in saved_groups:
				restore(room, parameter.GROUP, group)
