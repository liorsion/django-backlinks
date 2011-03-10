import re
import xmlrpclib
import urllib

from backlinks.exceptions import fault_code_to_client_error, \
    BacklinkClientError, BacklinkClientRemoteError, \
    BacklinkClientConnectionError, BacklinkClientServerDoesNotExist,\
    BacklinkClientAccessDenied, BacklinkClientInvalidResponse
from backlinks.conf import settings
from backlinks.utils import url_reader

# See http://hixie.ch/specs/pingback/pingback#TOC2.3
PINGBACK_RE = re.compile(r'<link rel="pingback" href="(?P<pingback_url>[^"]+)" ?/?>')


# Override the user agent for xmlrpclib's ServerProxy
class BacklinksTransport(xmlrpclib.Transport):
    user_agent = settings.USER_AGENT_STRING

class BacklinksSafeTransport(xmlrpclib.SafeTransport):
    user_agent = settings.USER_AGENT_STRING

# Build a nice ServerProxy replacement that will use our transport classes
class BacklinksServerProxy(xmlrpclib.ServerProxy):
    transport_class = BacklinksTransport
    safe_transport_class = BacklinksSafeTransport

    def __init__(self, uri, transport=None, encoding=None, verbose=0,
                 allow_none=0, use_datetime=0):
        type, uri = urllib.splittype(uri)
        if type not in ("http", "https"):
            raise IOError("unsupported XML-RPC protocol")
        self.__host, self.__handler = urllib.splithost(uri)
        if not self.__handler:
            self.__handler = "/RPC2"

        if transport is None:
            if type == "https":
                transport = self.safe_transport_class(use_datetime=use_datetime)
            else:
                transport = self.transport_class(use_datetime=use_datetime)
        self.__transport = transport

        self.__encoding = encoding
        self.__verbose = verbose
        self.__allow_none = allow_none

    def __request(self, methodname, params):
        # call a method on the remote server

        request = xmlrpclib.dumps(params, methodname, encoding=self.__encoding,
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
        return xmlrpclib._Method(self.__request, name)


class PingbackClient(object):
    """
    A client for the Pingback protocol.

    """
    # Default proxy class
    proxy_class = BacklinksServerProxy

    def __init__(self, proxy_class=None):
        self.proxy_class = proxy_class or self.proxy_class

    def autodiscover(self, link, response):
        """
        Determine the Pingback server URL for a given response for a resource.

        """
        pingback_url = response.headers.getheader('x-pingback', None)
        if not pingback_url:
            match = PINGBACK_RE.search(response.body)
            if match:
                pingback_url = match.group('pingback_url')
        return pingback_url

    def ping(self, ping_url, target_url, source_url, verbose=False, *args, **kwargs):
        """
        Attempt to ping a resource using the given Pingback server URL.

        """
        try:
            server = self.proxy_class(ping_url, verbose=verbose)
            result = server.pingback.ping(source_url, target_url)
            return True
        except xmlrpclib.Fault, e:
            exception_class = fault_code_to_client_error.get(int(e.faultCode),
                                                             BacklinkClientError)
            raise exception_class(reason=e.faultString)
        except xmlrpclib.ProtocolError, e:
            if e.errcode == 404:
                raise BacklinkClientServerDoesNotExist
            elif e.errcode == 500:
                raise BacklinkClientRemoteError
            elif e.errcode in (401, 403):
                raise BacklinkClientAccessDenied
            raise BacklinkClientConnectionError(reason=e.errmsg)
        except xmlrpclib.ResponseError, e:
            raise BacklinkClientInvalidResponse(reason=e.message)
        except Exception, e:
            raise BacklinkClientError(reason=str(e))

# A default instance of the Pingback client for convenience.
default_client = PingbackClient()
