"""Client for the embedded /rest.php API (not the monitoring cloud API)."""

import json
import math
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class WebApiError(RuntimeError):
	"""HTTP, JSON, authentication or controller-reported failure."""


class _NoRedirect(HTTPRedirectHandler):
	def redirect_request(self, req, fp, code, msg, headers, newurl):
		# Never forward credentials/session data to another endpoint.
		return None


class ControllerWebClient:
	DEFAULT_TIMEOUT = 10.0
	MAX_RESPONSE_BYTES = 2 * 1024 * 1024

	def __init__(self, base_url, login='admin', password='admin', timeout=DEFAULT_TIMEOUT):
		parts = urlsplit(base_url)
		if (parts.scheme not in ('http', 'https') or not parts.hostname
				or parts.username is not None or parts.password is not None
				or parts.query or parts.fragment or parts.path not in ('', '/')):
			raise ValueError('Web URL must be an http(s) origin, e.g. http://192.168.1.50')
		parts.port  # Validate the optional port before making requests.
		if not math.isfinite(timeout) or timeout <= 0:
			raise ValueError('HTTP timeout must be finite and positive')
		self.base_url = base_url.rstrip('/')
		self._login = login
		self._password = password
		self.timeout = timeout
		self._session = None
		# Local controller traffic must not use OS/environment HTTP proxies.
		self._opener = build_opener(ProxyHandler({}), _NoRedirect())

	def _request(self, method, path, payload=None):
		if not path.startswith('/') or path.startswith('//') or '#' in path:
			raise ValueError('Expected an absolute local HTTP path')
		body = None if payload is None else json.dumps(payload).encode('utf-8')
		request = Request(self.base_url + path, data=body, method=method,
			headers={'Content-Type': 'application/json', 'Accept': 'application/json',
				'Connection': 'close'})
		try:
			with self._opener.open(request, timeout=self.timeout) as response:
				data = response.read(self.MAX_RESPONSE_BYTES + 1)
		except HTTPError as exc:
			code = exc.code
			exc.close()
			raise WebApiError(f'{method}: HTTP {code}') from None
		except (URLError, OSError, ValueError) as exc:
			# Do not expose request bodies, passwords, sessions or server HTML.
			raise WebApiError(f'{method}: transport failure ({type(exc).__name__}); '
				'command outcome may be unknown, read back via CAN') from None
		if len(data) > self.MAX_RESPONSE_BYTES:
			raise WebApiError('HTTP response exceeds size limit')
		return data

	def get(self, path='/'):
		"""Fetch a local resource as bytes; binding operations always use POST."""
		return self._request('GET', path)

	def post(self, mode, **fields):
		payload = dict(fields, mode=mode)
		if mode != 'login':
			if self._session is None:
				raise WebApiError('Not authenticated')
			payload['session'] = self._session
		data = self._request('POST', '/rest.php', payload)
		try:
			result = json.loads(data)
		except (ValueError, UnicodeError):
			raise WebApiError(f'{mode}: invalid JSON response') from None
		if not isinstance(result, dict):
			raise WebApiError(f'{mode}: expected a JSON object')
		if result.get('status') == 'not logged in':
			self._session = None
			raise WebApiError(f'{mode}: session rejected')
		if result.get('error') or result.get('errors'):
			raise WebApiError(f'{mode}: controller reported an error')
		if 'status' in result and result['status'] != 'ok':
			raise WebApiError(f'{mode}: unexpected response status')
		return result

	def login(self):
		self._session = None
		result = self.post('login', login=self._login, password=self._password, long=0)
		session = result.get('session_id')
		if result.get('status') != 'ok' or type(session) is not int or not 0 < session <= 0xFFFFFFFF:
			raise WebApiError('login: invalid session response')
		self._session = session

	def logout(self):
		try:
			if self._session is not None:
				self.post('logout')
		finally:
			self._session = None

	def config(self):
		result = self.post('config')
		if not isinstance(result.get('controllers'), list):
			raise WebApiError('config: missing controllers array')
		return result

	def _binding(self, mode, **fields):
		result = self.post(mode, **fields)
		if not isinstance(result.get('controllers'), list):
			raise WebApiError(f'{mode}: missing controllers array')
		return result

	def bind_input(self, program_id, input_id, controller_id, sensor_id):
		return self._binding('bind_input', program_id=program_id, input=input_id,
			host_type=0, host_id=controller_id, io_id=sensor_id)

	def unbind_input(self, program_id, input_id):
		return self._binding('unbind_input', program_id=program_id, input=input_id)

	def bind_relay(self, controller_id, relay_id, program_id, output_id):
		return self._binding('bind_relay', controller_id=controller_id, relay=relay_id,
			program_id=program_id, output=output_id)

	def unbind_relay(self, controller_id, relay_id):
		return self._binding('unbind_relay', controller_id=controller_id, relay=relay_id)