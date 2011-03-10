import urllib
import urllib2
import zlib
import socket
import re

CHARSET_RE = re.compile(r'charset=([-\w]+)', re.IGNORECASE)

class SmartRedirectHandler(urllib2.HTTPRedirectHandler):
    def http_error_301(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_301(self, req, fp, code, msg, headers)
        result.status = code
        return result

    def http_error_302(self, req, fp, code, msg, headers):
        result = urllib2.HTTPRedirectHandler.http_error_302(self, req, fp, code, msg, headers)
        result.status = code
        return result


class DefaultErrorHandler(urllib2.HTTPDefaultErrorHandler):
    def http_error_default(self, req, fp, code, msg, headers):
        result = urllib2.HTTPError(req.get_full_url(), code, msg, headers, fp)
        result.status = code
        return result


class GzipStream(object):
    def __init__(self, fp):
        self.buf = ''
        self.fp = fp
        self.dc = zlib.decompressobj(16+zlib.MAX_WBITS)
    
    def read(self, max_length=None):
        # Prime the read buffer
        buf_len = len(self.buf)
        # Make sure we grab enough compressed data
        chunk_size = (max_length + 1024) if max_length else 0
        if (buf_len < chunk_size) or buf_len == 0:
            if max_length:
                self.buf = self.buf + self.fp.read(chunk_size - buf_len)
            else:
                self.buf = self.fp.read()
        # Decompress read buffer
        if len(self.buf) > 0:
            if max_length:
                result = self.dc.decompress(self.buf, max_length)
                self.buf = self.dc.unconsumed_tail
            else:
                result = self.dc.decompress(self.buf)
        else:
            result = self.dc.flush()
        return result


class ResponseWrapper(object):
    def __init__(self, response):
        self.raw_response = response
        self.url = response.url
        self.fp = response.fp
        self.headers = response.headers
        if self.headers.getheader('content-encoding', None) == 'gzip':
            self.stream = GzipStream(self.fp)
            self._read = self.stream.read
        else:
            self.stream = None
            self._read = self.fp.read
        self._body = ''
        self._charset = None

    def read(self, max_length=None):
        chunk = self._read(max_length)
        self._body = self._body + chunk
        return chunk

    def close(self):
        self.read = None
        if self.stream:
            self.stream = None
        if self.fp:
            self.fp.close()
        self.fp = None

    def _get_body(self):
        if not self._body:
            self.read()
        return self._body

    body = property(_get_body)

    def _get_charset(self):
        if not self._charset:
            content_type = self.headers.getheader('content-type', None)
            if content_type:
                charset_match = CHARSET_RE.search(content_type)
                if charset_match:
                    self._charset = charset_match.group(1)
            else:
                # TODO: make this use a proper parser?
                charset = CHARSET_RE.search(self.body)
                if charset:
                    self._charset = charset.group(1)
        return self._charset

    charset = property(_get_charset)

        
class URLReader(object):
    """
    A simple class which builds an urllib2 URL opener, adding some sensible
    default request headers, and returns a ResponseWrapper object.

    """

    DEFAULT_HEADERS = {
        'Accept-Encoding': 'gzip',
        'Accept-Charset': 'utf-8',
        'Accept': 'text/xml,application/xml,application/xhtml+xml,text/html',
    }
    DEFAULT_TIMEOUT = 30
    RESPONSE_CLASS = ResponseWrapper

    def __init__(self, extra_headers={}, timeout=None):
        self._headers = extra_headers
        self._headers.update(self.DEFAULT_HEADERS)
        self.timeout = timeout or self.DEFAULT_TIMEOUT
        self._opener = urllib2.build_opener(urllib2.HTTPHandler(debuglevel=0),
                                            urllib2.HTTPCookieProcessor(),
                                            SmartRedirectHandler())

    def open(self, url, data=None, extra_headers={}, timeout=None):
        # Build request headers
        request_headers = {}
        request_headers.update(extra_headers)
        request_headers.update(self._headers)
        
        # Build POST data
        if data:
            data = urllib.urlencode(data)
        request = urllib2.Request(url, data, request_headers)

        # Perform request
        socket.setdefaulttimeout(timeout or self.timeout)
        response = self._opener.open(request)
        return self.RESPONSE_CLASS(response)
