"""Launch the dedicated HTTP/CAN binding bench dashboard."""


def main():
	try:
		from gui.web_bindings import main as launch
	except ImportError as error:
		if error.name in ('tkinter', '_tkinter'):
			raise SystemExit('Tkinter отсутствует: установите Tcl/Tk для используемого Python.') from None
		raise
	launch()


if __name__ == '__main__':
	main()