"""Headless physical checks and tests of the actual firmware reserve FSM."""

import os
from pathlib import Path
import shutil
import subprocess
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest
import smartnet.constants as snc
from smartnet.parameter_info.district_heating import PARAMETER_INFO
from simulator.boiler import Simulator as BoilerSimulator
from simulator.district_heating import Simulator as DistrictSimulator


ROOT = Path(__file__).resolve().parents[1]


def test_firmware_reserve_transitions(tmp_path):
	smartweb = Path(os.environ.get('SMARTWEB_SOURCE_DIR', ROOT.parent / 'SmartWeb'))
	header_dir = smartweb / 'src/shared/modules/mPrograms'
	compiler = os.environ.get('CXX') or shutil.which('g++')
	if not compiler and os.name == 'nt':
		candidate = Path('C:/Tools/Qt/5.15.2/Tools/mingw810_64/bin/g++.exe')
		compiler = str(candidate) if candidate.exists() else None
	if not compiler or not (header_dir / 'DistrictHeatingReserveControl.h').exists():
		pytest.skip('Requires C++ compiler and SmartWeb sources (SMARTWEB_SOURCE_DIR)')
	executable = tmp_path / ('reserve_test.exe' if os.name == 'nt' else 'reserve_test')
	env = dict(os.environ)
	env['PATH'] = str(Path(compiler).parent) + os.pathsep + env.get('PATH', '')
	result = subprocess.run([compiler, '-std=c++11', '-Wall', '-Wextra', '-Werror',
		'-I', str(header_dir), str(ROOT / 'tests/cpp/district_heating_reserve_test.cpp'),
		'-o', str(executable)], capture_output=True, text=True, env=env, timeout=60)
	assert result.returncode == 0, result.stdout + result.stderr
	result = subprocess.run([str(executable)], capture_output=True, text=True, env=env, timeout=30)
	assert result.returncode == 0, result.stdout + result.stderr
	assert 'transitions: OK' in result.stdout


def test_reserve_protocol_id_does_not_replace_valve_position():
	assert snc.DistrictHeatingParameterId.PARAM_CURRENT_MAXIMUM_BACKWARD_TEMPERATURE == 17
	assert snc.DistrictHeatingParameterId.PARAM_RESERVE_MODE == 19
	assert PARAMETER_INFO[snc.DistrictHeatingParameterId.PARAM_RESERVE_MODE]['type'] == 'UINT8_T'
	assert [int(mode) for mode in snc.DistrictHeatingReserveMode] == [0, 1, 2]


@pytest.mark.parametrize('mapped,value,expected', [
	(False, None, None), (True, None, False), (True, 0, False), (True, 255, True),
])
def test_reserve_valve_signal(mapped, value, expected):
	output = Mock()
	output.get_mapping.return_value = object() if mapped else None
	output.get_value.return_value = value
	program = Mock()
	program.get_output_channel.return_value = output
	simulator = DistrictSimulator.__new__(DistrictSimulator)
	simulator._program = program
	assert simulator.get_reserve_branch_open() is expected


@pytest.mark.parametrize('valve_open,expected_flow', [(False, 0), (True, 3), (None, 3)])
def test_closed_reserve_branch_blocks_boiler_flow(valve_open, expected_flow):
	program = Mock()
	program.get_id.return_value = 106
	program.get_max_flow_rate.return_value = 3000
	program.get_pump.return_value.is_mapped.return_value = True
	program.get_pump.return_value.get_value.return_value = 255
	settings = SimpleNamespace(getSource=lambda: 106)
	district = SimpleNamespace(_program=SimpleNamespace(
		get_type=lambda: snc.ProgramType.DISTRICT_HEATING,
		get_preset=lambda: SimpleNamespace(getSettings=lambda: settings)),
		get_reserve_branch_open=lambda: valve_open)
	simulator = BoilerSimulator.__new__(BoilerSimulator)
	simulator._program = program
	simulator._preset = object()
	simulator._control = SimpleNamespace(getSourceList=lambda: [district])
	assert simulator.get_flow() == expected_flow


def test_unrelated_boiler_not_isolated():
	simulator = BoilerSimulator.__new__(BoilerSimulator)
	simulator._preset = object()
	simulator._program = SimpleNamespace(get_id=lambda: 200)
	settings = SimpleNamespace(getSource=lambda: 106)
	district = SimpleNamespace(_program=SimpleNamespace(
		get_type=lambda: snc.ProgramType.DISTRICT_HEATING,
		get_preset=lambda: SimpleNamespace(getSettings=lambda: settings)),
		get_reserve_branch_open=lambda: False)
	simulator._control = SimpleNamespace(getSourceList=lambda: [district])
	assert simulator.reserve_branch_allows_flow()


@pytest.mark.parametrize('preset_name,mode', [
	('district_heating_reserve', snc.DistrictHeatingReserveMode.RESERVE_ONLY),
	('district_heating_supplement', snc.DistrictHeatingReserveMode.SUPPLEMENT_AND_RESERVE),
])
def test_new_presets_have_unique_channels_and_explicit_mode(preset_name, mode):
	from importlib import import_module
	with patch.dict(sys.modules, {'smartnet.remoteControl': SimpleNamespace(RemoteControlParameter=Mock())}):
		programs, _ = import_module(f'presets.list.{preset_name}').get_presets_list()
	district = next(p for p in programs if p.get_type() == snc.ProgramType.DISTRICT_HEATING)
	assert len(district.get_inputs()) == 8
	assert len(district.get_outputs()) == 5
	assert district.get_inputs()[7] is not None
	assert district.get_outputs()[4] is not None
	assert district.getSettings()._reserve_mode == mode
	for getter in ('get_inputs', 'get_outputs'):
		channels = [channel for program in programs for channel in getattr(program, getter)() if channel is not None]
		keys = [(channel._hostId, channel._channelId) for channel in channels]
		assert len(keys) == len(set(keys))