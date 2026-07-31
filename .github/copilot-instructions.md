# Copilot Instructions for BoilerRoomSimulator

## Environment

- **Operating system:** Windows
- **Preferred Python interpreter:** `C:\Tools\Python311\python.exe`
- Run commands from the repository root: `C:\development\BoilerRoomSimulator`
- Use PowerShell syntax for commands. When a command is shown with multiple operations, separate them with `;`.
- Do not assume that the Python executable on `PATH` is the project interpreter; use the full path above when validating changes.
- When inspecting project changes, always use `git --no-pager diff` rather than `git diff` so Git does not open an interactive pager.

Example:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe --version
```

## Project Overview

BoilerRoomSimulator is a Python simulator for SmartWeb-compatible heating-control systems. It communicates with controller abstractions over CAN and optionally exposes a CAN-over-UDP bridge. The simulator can run with a GUI or without one and can load presets and scenarios.

Important top-level areas:

- `main.py` — application entry point and command-line argument parsing.
- `mainThread.py` — application orchestration, controller setup, preset loading, and simulator startup.
- `controllers/` — controller discovery, controller communication, and virtual controller I/O.
- `programs/` — program models representing device types and their inputs, outputs, and parameters.
- `simulator/` — runtime behavior for program models, including boilers, rooms, heating circuits, cascades, DHW, and other simulated devices.
- `smartnet/` — SmartWeb protocol, CAN messaging, constants, channel mappings, and remote-control support.
- `presets/` — preset configuration loading and program/virtual-I/O definitions.
- `scenario/` — scripted scenario loading and execution.
- `config_parser/` — configuration parsing.
- `gui/` — optional GUI implementation.
- `functions/` — shared helper functionality.
- `udp/` — UDP bridge support.

A program model in `programs/` generally describes configuration and data channels. Its corresponding implementation in `simulator/` provides runtime behavior. `programs/factory.py` and `simulator/simulator.py` map protocol program-type names such as `BOILER`, `CASCADE_MANAGER`, and `HEATING_CIRCUIT` to their implementations.

## Running the Application

The primary entry point is `main.py`:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe main.py --help
```

Common options include:

- `--profile <name>` — select a program profile; the default is `main`.
- `--id <controller-id>` — select the controller ID to control.
- `--udp [port]` — enable the CAN-over-UDP bridge; the default bridge port is `31987` when the option is supplied without a value.
- `--no-gui` — run without the GUI.
- `--scenario [name]` — enable scenario execution.
- `--can [config]` — select a CAN-bus configuration.
- `--preset <name>` — load a specific preset at startup.
- `--debug` — enable the simulator debug responder.

## Dependencies

Dependency declarations currently exist in both `pyproject.toml` and `requirements.txt`. Keep them consistent when adding or removing runtime dependencies. The repository includes dependencies for Django, formatting, CAN communication, and GUI support; GUI and CAN imports may require platform-specific installation.

Use the project interpreter when installing or inspecting packages:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe -m pip install -r requirements.txt
C:\Tools\Python311\python.exe -m pip show python-can wxPython
```

Do not install packages globally with a different Python executable. Prefer a virtual environment for dependency experiments, but continue using the documented interpreter for authoritative checks unless the environment has been intentionally changed.

## Coding Conventions

- Preserve the existing tab-based indentation in Python files unless a file is being intentionally reformatted.
- Preserve public method names and protocol strings; program-type strings are part of the SmartWeb integration contract.
- Use standard Python `snake_case` naming for new functions, methods, variables, and internal attributes.
- Move existing camelCase names toward `snake_case` gradually, as part of related changes rather than through broad standalone renames.
- Preserve existing public method names and compatibility aliases until all callers and integrations have migrated. Many older classes use camelCase methods; do not rename them casually.
- Keep protocol strings, program-type names, parameter IDs, and other externally observable identifiers unchanged even when Python wrapper names are modernized.
- Keep protocol and simulator responsibilities separate: protocol/message changes belong in `smartnet/`, model changes in `programs/`, and runtime behavior changes in `simulator/`.
- When adding a new simulated program type, update the model factory and simulator type mapping, then check presets, channel definitions, and controller interactions.
- Treat parameter indexes, channel indexes, program IDs, and CAN/UDP packet layouts as externally observable values. Do not renumber them casually.
- Avoid broad cleanup or reformatting unrelated to the requested change.

## Validation

Use targeted validation with the confirmed interpreter. At minimum, compile changed Python files:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe -m py_compile path\to\changed_file.py
```

For broader syntax validation:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe -m compileall -q .
```

Before running the application, inspect whether the selected preset, GUI, CAN backend, UDP bridge, or external controller is required. Prefer `--no-gui` for headless checks. Do not claim that a simulator run or integration test passed unless its required hardware, GUI, network, and preset dependencies were actually available.

When changing protocol behavior, validate both message construction and parsing where practical. When changing simulator behavior, validate boundary cases such as missing mappings, empty presets, invalid program IDs, and indexed parameters.

## Change Review Checklist

- [ ] The change is limited to the relevant component.
- [ ] Protocol names, IDs, indexes, and mappings remain compatible.
- [ ] Imports work with `C:\Tools\Python311\python.exe`.
- [ ] Changed files pass targeted `py_compile` checks.
- [ ] Relevant existing scripts or application paths were exercised when their dependencies were available.
- [ ] No generated files, build artifacts, caches, or binaries were modified unintentionally.
