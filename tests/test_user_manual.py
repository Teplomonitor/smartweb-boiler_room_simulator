"""Validate generated documentation without starting the simulator or GUI."""

import re
import unittest
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET

from tools import build_user_manual as builder


class UserManualTests(unittest.TestCase):
	def test_source_links_and_images(self):
		text = builder.SOURCE.read_text(encoding='utf-8')
		images = re.findall(r'^!\[([^\]]+)\]\(([^)]+)\)$', text, re.MULTILINE)
		self.assertEqual(len(images), 9)
		for caption, relative in images:
			self.assertTrue(caption.startswith('Рисунок '))
			width, height = builder.png_size(builder.SOURCE.parent / relative)
			self.assertGreater(width, 0)
			self.assertGreater(height, 0)
		for target in re.findall(r'\]\(([^)]+)\)', text):
			self.assertTrue((builder.SOURCE.parent / target).is_file(), target)

	def test_odt_package_and_embedded_images(self):
		with zipfile.ZipFile(builder.OUTPUT) as archive:
			self.assertIsNone(archive.testzip())
			self.assertEqual(archive.infolist()[0].filename, 'mimetype')
			self.assertEqual(archive.infolist()[0].compress_type, zipfile.ZIP_STORED)
			for name in ('content.xml', 'styles.xml', 'meta.xml', 'META-INF/manifest.xml'):
				ET.fromstring(archive.read(name))
			images = [name for name in archive.namelist() if name.startswith('Pictures/')]
			self.assertEqual(len(images), 9)
			for name in images:
				self.assertEqual(archive.read(name),
					(builder.SOURCE.parent / 'images' / Path(name).name).read_bytes())

	def test_odt_headings_and_contents(self):
		with zipfile.ZipFile(builder.OUTPUT) as archive:
			root = ET.fromstring(archive.read('content.xml'))
		headings = [''.join(item.itertext()) for item in root.findall('.//text:h', builder.NS)]
		expected = [re.sub(r'^#{1,3} ', '', line) for line in
			builder.SOURCE.read_text(encoding='utf-8').splitlines() if line.startswith('#')]
		self.assertEqual(headings, expected)
		bookmarks = root.findall('.//text:bookmark', builder.NS)
		self.assertEqual(len(bookmarks), 13)
		links = root.findall('.//text:a', builder.NS)
		internal = [item for item in links if item.get(f'{{{builder.NS["xlink"]}}}href', '').startswith('#')]
		self.assertEqual(len(internal), len(bookmarks))

	def test_vector_diagrams(self):
		for name in ('can_connection', 'udp_connection'):
			path = builder.SOURCE.parent / 'images' / (name + '.svg')
			root = ET.parse(path).getroot()
			self.assertEqual(root.attrib['viewBox'], '0 0 1400 700')
			self.assertGreater(len(root.findall('{http://www.w3.org/2000/svg}text')), 10)

	def test_pdf_text_images_and_commands(self):
		try:
			from pypdf import PdfReader
		except ImportError:
			self.skipTest('Optional pypdf is required for PDF validation')
		reader = PdfReader(builder.OUTPUT.with_suffix('.pdf'))
		text = '\n'.join(page.extract_text() or '' for page in reader.pages)
		compact = re.sub(r'\s+', '', text)
		self.assertGreaterEqual(len(reader.pages), 15)
		self.assertIn('BoilerRoomSimulator', text)
		source = builder.SOURCE.read_text(encoding='utf-8')
		for heading in re.findall(r'^## (.+)$', source, re.MULTILINE):
			self.assertIn(re.sub(r'\s+', '', heading), compact)
		for code in re.findall(r'```powershell\n(.*?)\n```', source, re.DOTALL):
			for line in code.splitlines():
				self.assertIn(re.sub(r'\s+', '', line), compact)
		for index in range(1, 10):
			self.assertIn('Рисунок%d.' % index, compact)
		images = set()
		for page in reader.pages:
			resources = page.get('/Resources', {})
			objects = resources.get('/XObject', {})
			for reference in objects.values():
				if reference.get_object().get('/Subtype') == '/Image':
					images.add((reference.idnum, reference.generation))
		self.assertEqual(len(images), 9)
		print('\nPDF validated: %d pages, %d images; all section headings and commands found.' %
			(len(reader.pages), len(images)))


if __name__ == '__main__':
	unittest.main()