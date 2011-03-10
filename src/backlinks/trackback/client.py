import re
from urllib2 import HTTPError, URLError
from xml.sax import parseString, SAXParseException
from xml.sax.handler import ContentHandler

from backlinks.utils import url_reader
from backlinks.exceptions import BacklinkClientError, \
    BacklinkClientAccessDenied, BacklinkClientServerDoesNotExist, \
    BacklinkClientConnectionError, BacklinkClientRemoteError, \
    BacklinkClientInvalidResponse


RDF_RE = re.compile(r'(<rdf:RDF .*?</rdf:RDF>)', re.DOTALL)
TRACKBACK_PING_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'

class RDFHandler(ContentHandler):
    """
    Parser for TrackBack autodiscovery RDF documents.

    """
    def startDocument(self):
        self.ping_url = None
        self.identifier = None

    def startElement(self, name, attrs):
        if name == 'rdf:Description':
            ping_url = attrs.get('trackback:ping', None)
            identifier = attrs.get('dc:identifier', None)
            if ping_url and identifier:
                self.identifier = identifier
                self.ping_url = ping_url


class TrackBackResponseHandler(ContentHandler):
    """
    Parser for TrackBack server responses.

    """
    def startDocument(self):
        self._error = False
        self.errors = False
        self._message = False
        self.message = ''

    def startElement(self, name, attrs):
        if name == 'error':
            self._error = True
        if name == 'message':
            self._message = True
            
    def endElement(self, name):
        if name == 'error':
            self._error = False
        if name == 'message':
            self._message = False
            
    def characters(self, content):
        if self._error:
            try:
                errors = int(content)
                self.errors = bool(errors)
            except ValueError:
                pass
        if self._message:
            self.message = content


class TrackBackClient(object):
    """
    A TrackBack protocol client.

    """
    def __init__(self, url_opener=url_reader.open, response_handler=TrackBackResponseHandler()):
        self.url_opener = url_opener
        self.response_handler = response_handler

    def autodiscover(self, link, response):
        """
        Attempt to determine the TrackBack server URL for a resource by
        checking a response for the existence of a TrackBack autodiscovery
        RDF document.

        """
        trackback_url = None
        rdfs = RDF_RE.findall(response.body)
        for rdf in rdfs:
            try:
                handler = RDFHandler()
                parseString(rdf, handler)
                if handler.ping_url:
                    if handler.identifier == link:
                        trackback_url = handler.ping_url
                        break
            except SAXParseException:
                pass
        return trackback_url

    def do_ping_request(self, ping_url, data):
        """
        Make the TrackBack HTTP POST ping request with appropriate data.

        """
        return self.url_opener(ping_url, data, {'Content-Type': TRACKBACK_PING_CONTENT_TYPE})

    def validate_response(self, response):
        """
        Ensure the TrackBack server returned a valid, non-error TrackBack
        XML response.

        """
        try:
            parseString(response.body, self.response_handler)
            if self.response_handler.errors:
                # An error response was returned, so pass along the given reason
                raise BacklinkClientError(reason=self.response_handler.message)
            return True
        except SAXParseException, e:
            raise BacklinkClientInvalidResponse


    def ping(self, ping_url, target_url, source_url, title=None, excerpt=None, *args, **kwargs):
        """
        Perform a TrackBack ping request.

        """
        # Build ping parameters
        ping_params = {'url': source_url}
        if title:
            ping_params['title'] = title
        if excerpt:
            ping_params['excerpt'] = excerpt

        # Attempt the ping
        try:
            response = self.do_ping_request(ping_url, ping_params)
        except HTTPError, e:
            if e.code == 404:
                raise BacklinkClientServerDoesNotExist
            elif e.code == 500:
                raise BacklinkClientRemoteError
            elif e.code in (403, 401):
                raise BaclinkClientAccessDenied
            raise BacklinkClientConnectionError(reason=e.msg)
        except URLError, e:
            raise BacklinkClientConnectionError(reason=e.reason)

        # Validate the response
        return self.validate_response(response)

# A default client instance for convenience
default_client = TrackBackClient()
