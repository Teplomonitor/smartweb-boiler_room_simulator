# CANable GS-USB on Windows

The simulator uses `python-can`'s `gs_usb` backend for adapters shown by
Device Manager as **canable gs_usb**. The profiles in `can.ini` configure the
CAN bus for 20,000 bit/s:

- `canable0`: first GS-USB adapter (`index = 0`, legacy positional profile)
- `canable1`: second GS-USB adapter (`index = 1`, legacy positional profile)

On the current machine, `tools/list_gs_usb.py` identifies the two devices as:

- `ucan`: **UCAN USB to CAN adapter**, GS-USB `index = 0`;
- `candleLightGsUsb`: **candleLight USB to CAN adapter**, GS-USB `index = 1`.

Both devices use `gs_usb` (`VID_1D50`, `PID_606F`). The named profiles match the USB product name at startup and resolve the current index automatically. They are not additional devices: the parallel coordinator rejects two profiles that currently select the same adapter. If multiple identical adapters share a product name, set `serial = ...` in each named profile to disambiguate them. Missing or ambiguous matches prevent startup.

## Install software

Install the project dependencies with the documented Python interpreter:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe -m pip install -r requirements.txt
```

The adapter must use a Windows USB driver supported by PyUSB. If Windows
does not expose the device to the GS-USB backend, use Zadig to install
WinUSB or libusbK for the **canable gs_usb** device. Do not replace working
GS-USB firmware with the CandleLight firmware merely to change the driver.

Check which adapters are visible before starting the simulator:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe tools\list_gs_usb.py
```

The utility only enumerates devices and does not transmit CAN frames. It shows
product, serial number, USB path and current index. Named profiles do not need
index edits after reconnecting adapters; numbered profiles remain positional.

## Start the simulator

For the first adapter:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe main.py --can canable0
```

For the second adapter in another simulator process:

```powershell
Set-Location C:\development\BoilerRoomSimulator
C:\Tools\Python311\python.exe main.py --can canable1
```

The current application creates one CAN bus per process, so separate
processes can use separate adapters. Do not start both processes with the
same profile. Use `ucan` and `candleLightGsUsb` for stable device selection;
the numbered profiles depend on enumeration order after reconnection.

## Bitrate and wiring

The configured bitrate is **20,000 bit/s** and must match every device on the
physical CAN bus. The USB driver does not normally impose this bitrate;
`python-can` asks the GS-USB firmware to configure it. If opening a bus at
20,000 bit/s fails, update the adapter firmware or use firmware known to
support that timing rather than changing the controller bitrate.

Connect CANH to CANH, CANL to CANL, and GND where required by the adapter and
controller. The physical bus should have exactly two 120-ohm termination
resistors, one at each end. Close other CAN tools before starting the
simulator so they do not claim the adapter or alter bus timing.

The existing `candleLight` profile is retained for a device using the legacy
`candle` backend. It is **not** the profile for the currently connected
"candleLight USB to CAN adapter", which enumerates as GS-USB and should use
`candleLightGsUsb` instead.