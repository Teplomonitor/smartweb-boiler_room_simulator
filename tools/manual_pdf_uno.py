"""Office-side PDF helper; compatible with OpenOffice's bundled Python 2.7.

Run only through build_user_manual.py, using its private named-pipe session.
"""

from __future__ import print_function

import sys
import time


def main():
	import uno
	from com.sun.star.beans import PropertyValue

	pipe, source_url, target_url = sys.argv[1:]
	context = uno.getComponentContext()
	resolver = context.ServiceManager.createInstanceWithContext(
		'com.sun.star.bridge.UnoUrlResolver', context)
	remote = None
	for attempt in range(60):
		try:
			remote = resolver.resolve(
				'uno:pipe,name=%s;urp;StarOffice.ComponentContext' % pipe)
			break
		except Exception:
			time.sleep(0.5)
	if remote is None:
		raise RuntimeError('Private office session did not become available')
	desktop = remote.ServiceManager.createInstanceWithContext(
		'com.sun.star.frame.Desktop', remote)

	def properties(**values):
		result = []
		for name, value in values.items():
			prop = PropertyValue()
			prop.Name = name
			prop.Value = value
			result.append(prop)
		return tuple(result)

	document = None
	try:
		document = desktop.loadComponentFromURL(source_url, '_blank', 0,
			properties(Hidden=True, ReadOnly=True, UpdateDocMode=0,
				MacroExecutionMode=4))
		if document is None:
			raise RuntimeError('Office could not load the manual')
		document.storeToURL(target_url,
			properties(FilterName='writer_pdf_Export', Overwrite=True))
		print('PDF exported by UNO')
	finally:
		try:
			if document is not None:
				document.close(True)
		finally:
			desktop.terminate()


if __name__ == '__main__':
	main()