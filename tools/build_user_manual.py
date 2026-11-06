"""Build the BRS manual (a deliberately limited Markdown subset) without hardware.

ODT uses only the standard library. Drawing PNG diagrams requires Pillow;
PDF conversion requires OpenOffice/LibreOffice. Existing screenshots are not edited.
"""

import argparse
import html
import os
import re
import struct
import subprocess
import tempfile
import uuid
import zipfile
from pathlib import Path
import xml.etree.ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'docs' / 'user_manual.md'
OUTPUT = ROOT / 'docs' / 'BoilerRoomSimulator_Manual_updated.odt'
NS = {
	'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0',
	'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
	'style': 'urn:oasis:names:tc:opendocument:xmlns:style:1.0',
	'fo': 'urn:oasis:names:tc:opendocument:xmlns:xsl-fo-compatible:1.0',
	'draw': 'urn:oasis:names:tc:opendocument:xmlns:drawing:1.0',
	'svg': 'urn:oasis:names:tc:opendocument:xmlns:svg-compatible:1.0',
	'xlink': 'http://www.w3.org/1999/xlink',
	'dc': 'http://purl.org/dc/elements/1.1/',
	'meta': 'urn:oasis:names:tc:opendocument:xmlns:meta:1.0',
	'manifest': 'urn:oasis:names:tc:opendocument:xmlns:manifest:1.0',
}
for prefix, uri in NS.items():
	ET.register_namespace(prefix, uri)


def node(parent, tag, text=None, **attrs):
	def qualified(name):
		prefix, local = name.split(':', 1)
		return f'{{{NS[prefix]}}}{local}'
	result = ET.SubElement(parent, qualified(tag), {
		qualified(key): str(value) for key, value in attrs.items()})
	result.text = text
	return result


def xml_bytes(root):
	return ET.tostring(root, encoding='utf-8', xml_declaration=True)


def inline(parent, value):
	"""Support bold, inline code and links; leave ordinary text unchanged."""
	pattern = r'(\*\*[^*]+\*\*|`[^`]+`|\[[^\]]+\]\([^)]+\))'
	for part in re.split(pattern, value):
		if part.startswith('**') and part.endswith('**'):
			node(parent, 'text:span', part[2:-2], **{'text:style-name': 'Bold'})
		elif part.startswith('`') and part.endswith('`'):
			node(parent, 'text:span', part[1:-1], **{'text:style-name': 'Mono'})
		elif re.fullmatch(r'\[[^\]]+\]\([^)]+\)', part):
			label, target = re.fullmatch(r'\[([^\]]+)\]\(([^)]+)\)', part).groups()
			node(parent, 'text:a', label, **{'xlink:href': target, 'xlink:type': 'simple'})
		else:
			# Spans also preserve text following other inline elements.
			node(parent, 'text:span', part)


def make_styles():
	root = ET.Element(f'{{{NS["office"]}}}document-styles', {
		f'{{{NS["office"]}}}version': '1.2'})
	styles = node(root, 'office:styles')
	default = node(styles, 'style:default-style', **{'style:family': 'paragraph'})
	node(default, 'style:paragraph-properties', **{
		'fo:margin-bottom': '0.18cm', 'fo:line-height': '120%',
		'fo:orphans': '2', 'fo:widows': '2'})
	node(default, 'style:text-properties', **{
		'fo:font-family': 'Arial', 'fo:font-size': '11pt',
		'fo:language': 'ru', 'fo:country': 'RU', 'fo:color': '#253449'})

	def style(name, paragraph=None, text=None, family='paragraph'):
		item = node(styles, 'style:style', **{'style:name': name, 'style:family': family})
		if paragraph:
			node(item, 'style:paragraph-properties', **paragraph)
		if text:
			node(item, 'style:text-properties', **text)

	style('Body')
	style('Title', {'fo:margin-top': '2cm', 'fo:margin-bottom': '1cm'},
		{'fo:font-size': '26pt', 'fo:font-weight': 'bold', 'fo:color': '#174b79'})
	style('H2', {'fo:break-before': 'page', 'fo:keep-with-next': 'always',
		'fo:margin-bottom': '0.5cm'}, {'fo:font-size': '18pt', 'fo:font-weight': 'bold'})
	style('H3', {'fo:keep-with-next': 'always', 'fo:margin-top': '0.5cm'},
		{'fo:font-size': '13pt', 'fo:font-weight': 'bold'})
	style('ContentsTitle', {'fo:break-before': 'page', 'fo:keep-with-next': 'always'},
		{'fo:font-size': '18pt', 'fo:font-weight': 'bold'})
	style('Code', {'fo:background-color': '#f1f5f9', 'fo:padding': '0.12cm',
		'fo:line-height': '110%', 'fo:margin-bottom': '0cm'},
		{'fo:font-family': 'Consolas', 'fo:font-size': '8.5pt'})
	style('List', {'fo:margin-left': '0.45cm', 'fo:text-indent': '-0.35cm'})
	style('Figure', {'fo:text-align': 'center', 'fo:keep-with-next': 'always'})
	style('Caption', {'fo:text-align': 'center', 'fo:margin-bottom': '0.5cm'},
		{'fo:font-size': '10pt', 'fo:font-style': 'italic'})
	style('Footer', {'fo:text-align': 'center'}, {'fo:font-size': '9pt'})
	style('Bold', text={'fo:font-weight': 'bold'}, family='text')
	style('Mono', text={'fo:font-family': 'Consolas', 'fo:font-size': '10pt'}, family='text')
	automatic = node(root, 'office:automatic-styles')
	layout = node(automatic, 'style:page-layout', **{'style:name': 'A4'})
	node(layout, 'style:page-layout-properties', **{
		'fo:page-width': '21cm', 'fo:page-height': '29.7cm',
		'fo:margin-top': '1.8cm', 'fo:margin-bottom': '1.8cm',
		'fo:margin-left': '2cm', 'fo:margin-right': '2cm',
		'style:print-orientation': 'portrait'})
	masters = node(root, 'office:master-styles')
	master = node(masters, 'style:master-page', **{
		'style:name': 'Standard', 'style:page-layout-name': 'A4'})
	footer = node(master, 'style:footer')
	p = node(footer, 'text:p', 'BRS • Руководство пользователя • ', **{'text:style-name': 'Footer'})
	node(p, 'text:page-number', '1', **{'text:select-page': 'current'})
	return root


def png_size(path):
	with path.open('rb') as stream:
		header = stream.read(24)
	if header[:8] != b'\x89PNG\r\n\x1a\n' or header[12:16] != b'IHDR':
		raise ValueError(f'Expected PNG image: {path}')
	width, height = struct.unpack('>II', header[16:24])
	if not width or not height:
		raise ValueError(f'Invalid image dimensions: {path}')
	return width, height


def build_odt():
	lines = SOURCE.read_text(encoding='utf-8').splitlines()
	root = ET.Element(f'{{{NS["office"]}}}document-content', {
		f'{{{NS["office"]}}}version': '1.2'})
	body = node(node(root, 'office:body'), 'office:text')
	headings = [line[3:] for line in lines if line.startswith('## ')]
	images = {}
	heading_index = 0
	code = False
	contents_added = False
	pending = []

	def paragraph(value, style='Body'):
		p = node(body, 'text:p', **{'text:style-name': style})
		inline(p, value)
		return p

	def flush():
		if pending:
			paragraph(' '.join(pending))
			pending.clear()

	for line in lines:
		if line.startswith('```'):
			flush()
			code = not code
			continue
		if code:
			node(body, 'text:p', line or ' ', **{'text:style-name': 'Code'})
			continue
		if not line.strip():
			flush()
			continue
		if line.startswith('## ') and not contents_added:
			flush()
			paragraph('Содержание', 'ContentsTitle')
			for index, title in enumerate(headings, 1):
				p = node(body, 'text:p', **{'text:style-name': 'Body'})
				node(p, 'text:a', title, **{
					'xlink:href': f'#section-{index}', 'xlink:type': 'simple'})
			contents_added = True
		if line.startswith('#'):
			flush()
			match = re.fullmatch(r'(#{1,3}) (.+)', line)
			if not match:
				raise ValueError(f'Unsupported heading: {line}')
			depth, title = len(match[1]), match[2]
			p = node(body, 'text:h', **{
				'text:style-name': 'Title' if depth == 1 else f'H{depth}',
				'text:outline-level': depth})
			if depth == 2:
				heading_index += 1
				node(p, 'text:bookmark', **{'text:name': f'section-{heading_index}'})
			inline(p, title)
		elif line.startswith('!['):
			flush()
			match = re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)', line)
			if not match:
				raise ValueError(f'Unsupported image markup: {line}')
			caption, relative = match.groups()
			path = (SOURCE.parent / relative).resolve()
			if not path.is_relative_to(SOURCE.parent):
				raise ValueError(f'Image must be inside docs/: {path}')
			width, height = png_size(path)
			scale = min(17 / width, 16 / height)
			archive_path = 'Pictures/' + path.name
			if archive_path in images and images[archive_path] != path:
				raise ValueError(f'Duplicate image name: {path.name}')
			images[archive_path] = path
			p = node(body, 'text:p', **{'text:style-name': 'Figure'})
			frame = node(p, 'draw:frame', **{
				'draw:name': path.stem, 'text:anchor-type': 'as-char',
				'svg:width': f'{width * scale:.3f}cm', 'svg:height': f'{height * scale:.3f}cm'})
			node(frame, 'draw:image', **{
				'xlink:href': archive_path, 'xlink:type': 'simple',
				'xlink:show': 'embed', 'xlink:actuate': 'onLoad'})
			node(frame, 'svg:title', caption)
			paragraph(caption, 'Caption')
		elif line.startswith('- ') or re.match(r'^\d+\. ', line):
			flush()
			paragraph('• ' + line[2:] if line.startswith('- ') else line, 'List')
		else:
			pending.append(line)
	flush()
	if code:
		raise ValueError('Unclosed code fence')
	manifest = ET.Element(f'{{{NS["manifest"]}}}manifest', {
		f'{{{NS["manifest"]}}}version': '1.2'})
	entries = {'/': 'application/vnd.oasis.opendocument.text',
		'content.xml': 'text/xml', 'styles.xml': 'text/xml', 'meta.xml': 'text/xml',
		**{name: 'image/png' for name in images}}
	for name, media in entries.items():
		node(manifest, 'manifest:file-entry', **{
			'manifest:full-path': name, 'manifest:media-type': media})
	metadata = ET.Element(f'{{{NS["office"]}}}document-meta', {
		f'{{{NS["office"]}}}version': '1.2'})
	meta = node(metadata, 'office:meta')
	node(meta, 'dc:title', 'BoilerRoomSimulator — руководство пользователя')
	node(meta, 'dc:language', 'ru-RU')
	node(meta, 'dc:description', 'Редакция от 5 ноября 2026 года; источник docs/user_manual.md')
	node(meta, 'meta:generator', 'BRS documentation builder')
	# Build atomically; never overwrite the historical manual.
	with tempfile.TemporaryDirectory(dir=OUTPUT.parent) as directory:
		staged = Path(directory) / OUTPUT.name
		with zipfile.ZipFile(staged, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
			archive.writestr('mimetype', entries['/'], compress_type=zipfile.ZIP_STORED)
			archive.writestr('content.xml', xml_bytes(root))
			archive.writestr('styles.xml', xml_bytes(make_styles()))
			archive.writestr('meta.xml', xml_bytes(metadata))
			archive.writestr('META-INF/manifest.xml', xml_bytes(manifest))
			for name, path in images.items():
				archive.write(path, name)
		staged.replace(OUTPUT)
	print(f'ODT: {OUTPUT} ({len(images)} embedded images)')


class Diagram:
	"""Use the same shapes for editable SVG and its high-resolution PNG."""
	def __init__(self, title):
		from PIL import Image, ImageDraw, ImageFont
		self.image = Image.new('RGB', (1400, 700), '#ffffff')
		self.draw = ImageDraw.Draw(self.image)
		font_dir = Path('C:/Windows/Fonts')
		self.font = ImageFont.truetype(str(font_dir / 'arial.ttf'), 24)
		self.heading = ImageFont.truetype(str(font_dir / 'arialbd.ttf'), 32)
		self.svg = ['<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="700" viewBox="0 0 1400 700">',
			'<rect width="1400" height="700" fill="white"/>']
		self.text(700, 60, title, bold=True)

	def text(self, x, y, value, bold=False, color='#253449'):
		self.draw.text((x, y), value, font=self.heading if bold else self.font, fill=color, anchor='mm')
		self.svg.append(f'<text x="{x}" y="{y}" text-anchor="middle" dominant-baseline="central" '
			f'font-family="Arial,sans-serif" font-size="{32 if bold else 24}" '
			f'font-weight="{"bold" if bold else "normal"}" fill="{color}">{html.escape(value)}</text>')

	def box(self, x1, y1, x2, y2, lines):
		self.draw.rounded_rectangle((x1, y1, x2, y2), radius=18, fill='#eef5fc', outline='#174b79', width=3)
		self.svg.append(f'<rect x="{x1}" y="{y1}" width="{x2-x1}" height="{y2-y1}" '
			'rx="18" fill="#eef5fc" stroke="#174b79" stroke-width="3"/>')
		for index, line in enumerate(lines):
			self.text((x1+x2)//2, (y1+y2)//2 + (index-(len(lines)-1)/2)*38, line)

	def line(self, points, color='#174b79', dashed=False):
		if dashed:
			# These diagrams only use axis-aligned segments.
			for (x1, y1), (x2, y2) in zip(points, points[1:]):
				length = abs(x2-x1) + abs(y2-y1)
				for offset in range(0, length, 18):
					end = min(offset+10, length)
					self.draw.line([(x1+(x2-x1)*offset/length, y1+(y2-y1)*offset/length),
						(x1+(x2-x1)*end/length, y1+(y2-y1)*end/length)], fill=color, width=3)
		else:
			self.draw.line(points, fill=color, width=4)
		pairs = ' '.join(f'{x},{y}' for x, y in points)
		dash = ' stroke-dasharray="10 8"' if dashed else ''
		self.svg.append(f'<polyline points="{pairs}" fill="none" stroke="{color}" stroke-width="4"{dash}/>')

	def arrow(self, x1, x2, y):
		self.line([(x1, y), (x2, y)])
		for x, sign in ((x1, 1), (x2, -1)):
			self.line([(x+sign*12, y-8), (x, y), (x+sign*12, y+8)])

	def resistor(self, x):
		self.line([(x, 290), (x, 310)])
		self.line([(x, 335), (x, 355)])
		self.draw.rectangle((x-7, 310, x+7, 335), fill='white', outline='#174b79', width=3)
		self.svg.append(f'<rect x="{x-7}" y="310" width="14" height="25" '
			'fill="white" stroke="#174b79" stroke-width="3"/>')

	def save(self, name):
		directory = ROOT / 'docs' / 'images'
		directory.mkdir(exist_ok=True)
		(directory / f'{name}.svg').write_text('\n'.join(self.svg + ['</svg>']), encoding='utf-8')
		self.image.save(directory / f'{name}.png')
		print(f'Diagram: {name}.svg / {name}.png')


def draw_diagrams():
	can = Diagram('BRS: подключение через USB–CAN')
	can.box(40, 230, 360, 420, ['Компьютер', 'BoilerRoomSimulator'])
	can.box(450, 230, 760, 420, ['USB–CAN', 'адаптер'])
	can.box(1030, 230, 1360, 420, ['Контроллер', 'SmartWeb'])
	can.arrow(360, 450, 325)
	can.text(405, 285, 'USB')
	can.line([(760, 290), (1030, 290)], '#db7d22')
	can.line([(760, 355), (1030, 355)], '#168c78')
	can.text(895, 266, 'CANH', color='#b35b10')
	can.text(895, 388, 'CANL', color='#168c78')
	can.resistor(780)
	can.resistor(1010)
	can.text(745, 160, '120 Ом: конец шины')
	can.text(1110, 160, '120 Ом: конец шины')
	can.line([(780, 180), (780, 230)], dashed=True)
	can.line([(1010, 180), (1010, 230)], dashed=True)
	can.line([(605, 420), (605, 475), (1195, 475), (1195, 420)], color='#64748b', dashed=True)
	can.text(900, 510, 'GND — по документации устройств и типу развязки')
	can.text(700, 590, 'Скорость в GS-USB-профилях BRS: 20 000 бит/с')
	can.text(700, 630, 'Встроенные терминаторы учитываются; всего два. Питание и распиновка не показаны.')
	can.save('can_connection')
	udp = Diagram('BRS: подключение через CAN-over-UDP')
	udp.box(40, 240, 360, 420, ['Компьютер', 'BoilerRoomSimulator', 'CAN: virtual'])
	udp.box(535, 240, 865, 420, ['Локальная сеть', 'роутер / коммутатор', 'или сеть хост ↔ ВМ'])
	udp.box(1040, 240, 1360, 420, ['SmartWeb', 'контроллер или Qt', 'CAN-over-UDP bridge'])
	udp.arrow(360, 535, 330)
	udp.arrow(865, 1040, 330)
	udp.text(445, 285, 'Ethernet / Wi-Fi')
	udp.text(950, 285, 'Ethernet / Wi-Fi')
	udp.text(700, 160, 'UDP-порт совпадает с обеих сторон: например, 31987')
	udp.text(700, 490, 'Включить мост на SmartWeb; разрешить UDP в брандмауэре ПК')
	udp.text(700, 535, 'Обнаружение требует доступности широковещательных пакетов')
	udp.text(700, 590, 'Независимые устройства: разные порты, например 31987 и 31988')
	udp.text(700, 635, 'Это транспорт CAN-сообщений, а не HTTP-доступ к веб-интерфейсу.')
	udp.save('udp_connection')


def build_pdf(soffice):
	if not soffice.is_file():
		raise FileNotFoundError(f'Office executable not found: {soffice}')
	# A separate profile avoids using or closing the user's active Writer session.
	with tempfile.TemporaryDirectory(prefix='brs_manual_') as directory:
		work = Path(directory)
		pdf = work / OUTPUT.with_suffix('.pdf').name
		base = [str(soffice), f'-env:UserInstallation={(work / "profile").as_uri()}',
			'-headless', '-nologo', '-nofirststartwizard']
		office_python = soffice.parent / 'python.exe'
		if office_python.is_file() and (soffice.parent / 'uno.py').is_file():
			pipe = 'brs_manual_' + uuid.uuid4().hex
			process = subprocess.Popen(base + [
				f'-accept=pipe,name={pipe};urp;StarOffice.ServiceManager'],
				stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			try:
				result = subprocess.run([str(office_python),
					str(ROOT / 'tools' / 'manual_pdf_uno.py'), pipe,
					OUTPUT.as_uri(), pdf.as_uri()], capture_output=True, timeout=120,
					cwd=soffice.parent, env={**os.environ, 'PYTHONPATH': str(soffice.parent)})
			finally:
				try:
					process.wait(timeout=10)
				except subprocess.TimeoutExpired:
					# Only the private process tree started here, never the user's office.
					subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'],
						capture_output=True, timeout=15, check=False)
					process.wait(timeout=10)
		else:
			result = subprocess.run(base + ['--convert-to', 'pdf:writer_pdf_Export',
				'--outdir', str(work), str(OUTPUT)], capture_output=True, timeout=120)
		if result.returncode or not pdf.is_file() or pdf.read_bytes()[:5] != b'%PDF-':
			raise RuntimeError(f'PDF conversion failed: {result.stdout!r} {result.stderr!r}')
		pdf.replace(OUTPUT.with_suffix('.pdf'))
	print(f'PDF: {OUTPUT.with_suffix(".pdf")}')


def main():
	parser = argparse.ArgumentParser(description=__doc__)
	parser.add_argument('--draw-diagrams', action='store_true')
	parser.add_argument('--pdf', action='store_true')
	parser.add_argument('--soffice', type=Path, default=Path(
		'C:/Program Files (x86)/OpenOffice 4/program/soffice.exe'))
	args = parser.parse_args()
	if args.draw_diagrams:
		draw_diagrams()
	build_odt()
	if args.pdf:
		build_pdf(args.soffice)


if __name__ == '__main__':
	main()