import json
import socket
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler
from http.server import HTTPServer
from urllib.parse import urlparse, parse_qs

from settings import DEFAULT_HOST, DEFAULT_PORT


class BaseHttpHandler(BaseHTTPRequestHandler):

    def get(self, query_params: dict) -> 'response':
        DATA = {'msg': 'hello'}

        return response(status_code=200, data=DATA)

    def _handler_get(self):
        """Processing get request, call method get, response the client"""

        response = self.get(self.__query_parameters)

        self.send_response(response['status_code'])

        self.send_header('Content-type', response['content_type'])
        self.end_headers()

        self.wfile.write(json.dumps(response['data']).encode())

    @property
    def __query_parameters(self):
        """Return query parameters as a dictionary"""

        return parse_qs(urlparse(self.path).query)

    def handle_one_request(self):
        """
        Handle a single HTTP request.

        You normally don't need to override this method; see the class
        __doc__ string for information on how to handle specific HTTP
        commands such as GET and POST.
        """

        try:
            self.raw_requestline = self.rfile.readline(65537)

            if len(self.raw_requestline) > 65536:
                self.requestline, self.request_version, self.command = str()
                self.send_error(HTTPStatus.REQUEST_URI_TOO_LONG)
                return

            if not self.raw_requestline:
                self.close_connection = True
                return

            if not self.parse_request():
                # An error code has been sent, just exit
                return

            method_name = f'_handler_{self.command.lower()}'

            if not hasattr(self, method_name):
                self.send_error(HTTPStatus.NOT_IMPLEMENTED,
                                "Unsupported method (%r)" % self.command)
                return

            getattr(self, method_name)()

            self.wfile.flush()  # actually send the response if not already done.

        except socket.timeout as e:
            # a read or a write timed out.  Discard this connection
            self.log_error("Request timed out: %r", e)
            self.close_connection = True

            return


def run(handler_class: 'BaseRequestHandler', host: str = DEFAULT_HOST, port: int = DEFAULT_PORT):  # NOQA
    """Method for starting a server"""

    server_address = (host, port)
    httpd = HTTPServer(server_address, handler_class)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        httpd.server_close()


def response(status_code: int, data: dict, content_type: str = 'application/json') -> dict:
    """The method generates the response body"""

    return {
        'status_code': status_code,
        'data': data,
        'content_type': content_type
    }


run(BaseHttpHandler)
