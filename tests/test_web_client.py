import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from unittest.mock import Mock
from urllib.error import URLError

from webapi.client import ControllerWebClient, WebApiError


class WebClientTests(unittest.TestCase):
	def setUp(self):
		self.client = ControllerWebClient('http://127.0.0.1:8080', password='private-password')
		self.client._request = Mock(return_value=b'{"session_id":42,"status":"ok"}')
		self.client.login()
		self.client._request.reset_mock()

	def test_login_uses_numeric_short_session_flag(self):
		self.client._request.return_value = b'{"session_id":43,"status":"ok"}'
		self.client.login()
		self.client._request.assert_called_once_with('POST', '/rest.php', {
			'mode': 'login', 'login': 'admin', 'password': 'private-password', 'long': 0})

	def test_binding_payloads_and_session(self):
		self.client._request.return_value = b'{"partial":true,"controllers":[]}'
		operations = [
			(lambda: self.client.bind_input(101, 0, 7, 1),
				{'mode': 'bind_input', 'program_id': 101, 'input': 0,
					'host_type': 0, 'host_id': 7, 'io_id': 1}),
			(lambda: self.client.unbind_input(101, 0),
				{'mode': 'unbind_input', 'program_id': 101, 'input': 0}),
			(lambda: self.client.bind_relay(7, 0, 101, 1),
				{'mode': 'bind_relay', 'controller_id': 7, 'relay': 0, 'program_id': 101, 'output': 1}),
			(lambda: self.client.unbind_relay(7, 0),
				{'mode': 'unbind_relay', 'controller_id': 7, 'relay': 0}),
		]
		for operation, expected in operations:
			with self.subTest(mode=expected['mode']):
				operation()
				self.client._request.assert_called_with('POST', '/rest.php', dict(expected, session=42))

	def test_invalid_responses_are_not_successful(self):
		for data in (b'bad json', b'[]', b'{}', b'{"error":"private-password"}',
				b'{"errors":["private-password"]}', b'{"status":"fail"}'):
			with self.subTest(data=data):
				self.client._request.return_value = data
				with self.assertRaises(WebApiError) as error:
					self.client.unbind_input(101, 0)
				self.assertNotIn('private-password', str(error.exception))

	def test_invalid_login_session_is_rejected(self):
		for session in (0, -1, True, '42', None, 2 ** 32):
			self.client._request.return_value = json.dumps({'session_id': session, 'status': 'ok'})
			with self.assertRaises(WebApiError):
				self.client.login()

	def test_session_expiration_does_not_retry_or_reauthenticate(self):
		self.client._request.return_value = b'{"status":"not logged in"}'
		with self.assertRaisesRegex(WebApiError, 'session rejected'):
			self.client.unbind_relay(7, 0)
		self.client._request.assert_called_once()
		with self.assertRaisesRegex(WebApiError, 'Not authenticated'):
			self.client.config()
		self.client._request.assert_called_once()

	def test_logout_clears_session_even_on_error(self):
		self.client._request.side_effect = WebApiError('offline')
		with self.assertRaises(WebApiError):
			self.client.logout()
		self.assertIsNone(self.client._session)

	def test_timeout_has_no_automatic_retry_or_secret_leak(self):
		client = ControllerWebClient('http://127.0.0.1')
		client._session = 42
		client._opener.open = Mock(side_effect=URLError('private-password'))
		with self.assertRaises(WebApiError) as error:
			client.unbind_input(101, 0)
		client._opener.open.assert_called_once()
		self.assertNotIn('private-password', str(error.exception))
		self.assertIn('outcome may be unknown', str(error.exception))

	def test_invalid_origins_and_timeouts_are_rejected(self):
		for url in ('file:///test', 'http://user:pass@host', 'http://host/rest.php',
				'http://host?key=value', 'http://host#fragment', 'http://host:invalid'):
			with self.subTest(url=url), self.assertRaises(ValueError):
				ControllerWebClient(url)
		for timeout in (0, -1, float('inf'), float('nan')):
			with self.assertRaises(ValueError):
				ControllerWebClient('http://localhost', timeout=timeout)

	def test_local_http_get_post_and_no_redirects(self):
		requests = []
		class Handler(BaseHTTPRequestHandler):
			def log_message(self, *args):
				pass

			def do_GET(self):
				if self.path == '/redirect':
					self.send_response(302)
					self.send_header('Location', '/secret')
					self.end_headers()
					return
				requests.append(('GET', self.path))
				self.send_response(200)
				self.end_headers()
				self.wfile.write(b'controller page')

			def do_POST(self):
				payload = json.loads(self.rfile.read(int(self.headers['Content-Length'])))
				requests.append(('POST', self.path, payload))
				self.send_response(200)
				self.end_headers()
				self.wfile.write(b'{"status":"ok","session_id":42}')
		server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
		thread = threading.Thread(target=server.serve_forever, daemon=True)
		thread.start()
		try:
			client = ControllerWebClient(f'http://127.0.0.1:{server.server_port}')
			self.assertEqual(client.get(), b'controller page')
			client.login()
			self.assertEqual(requests[1][1], '/rest.php')
			self.assertEqual(requests[1][2]['password'], 'admin')
			with self.assertRaisesRegex(WebApiError, 'HTTP 302'):
				client.get('/redirect')
			self.assertEqual(len(requests), 2)
		finally:
			server.shutdown()
			server.server_close()
			thread.join()