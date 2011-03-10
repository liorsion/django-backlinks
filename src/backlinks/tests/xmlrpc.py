import urlparse
from xmlrpclib import ProtocolError, ServerProxy, _Method, getparser, dumps

from django.test.client import Client
from django.core.handlers.wsgi import STATUS_CODE_TEXT

class DjangoTestClientTransport(object):
    """
    A replacement XML-RPC transport class that uses the django
    test client to simulate HTTP interaction.

    """
    def __init__(self, use_datetime=0):
        self.client = Client()
        self._use_datetime = use_datetime

    def request(self, host, handler, request_body, verbose=0):
        self.verbose = verbose
        response = self.client.post(handler, request_body, content_type="text/xml")
        
        status_code, msg, headers = response.status_code, STATUS_CODE_TEXT.get(response.status_code, str(response.status_code)), response.items()

        if response.status_code != 200:
            raise ProtocolError(host + handler, status_code, msg, headers)
        
        return self._parse_response(response.content, None)
    
    def getparser(self):
        return getparser(use_datetime=self._use_datetime)

    def parse_response(self, file):
        return self._parse_response(file, None)

    def _parse_response(self, file, sock):
        parser, unmarshaller = self.getparser()
        if self.verbose:
            print "body:", repr(file)
        parser.feed(file)
        return unmarshaller.close()

class TestClientServerProxy(object):
    """
    A replacement for xmlrpclib.ServerProxy that knows how to use
    the test client transport class.

    """
    def __init__(self, uri, transport=DjangoTestClientTransport(), encoding=None, verbose=0, allow_none=0, use_datetime=0):
        self.__host, self.__handler = '', uri
        self.__transport = transport
        self.__encoding = encoding
        self.__verbose = verbose
        self.__allow_none = allow_none

    def __request(self, methodname, params):
        # call a method on the remote server

        request = dumps(params, methodname, encoding=self.__encoding,
                        allow_none=self.__allow_none)

        response = self.__transport.request(
            self.__host,
            self.__handler,
            request,
            verbose=self.__verbose
            )

        if len(response) == 1:
            response = response[0]

        return response

    def __repr__(self):
        return (
            "<ServerProxy for %s%s>" %
            (self.__host, self.__handler)
            )

    __str__ = __repr__

    def __getattr__(self, name):
        # magic method dispatcher
        return _Method(self.__request, name)
