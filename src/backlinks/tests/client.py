from urllib import urlencode
from urllib2 import HTTPError

from django import test
from django.test.client import Client

from backlinks.exceptions import BacklinkClientError,\
    BacklinkClientConnectionError, BacklinkClientRemoteError,\
    BacklinkClientServerDoesNotExist, BacklinkClientInvalidResponse,\
    BacklinkClientAlreadyRegistered
from backlinks.client import BacklinksClient
from backlinks.pingback.client import PingbackClient
from backlinks.trackback.client import TrackBackClient
from backlinks.tests.mock import mock_reader
from backlinks.tests.xmlrpc import TestClientServerProxy

class PingbackClientTestCase(test.TestCase):
    fixtures = ['backlinks_test_data.json']
    urls = 'backlinks.tests.client_urls'

    def setUp(self):
        self.pingback_client = PingbackClient(proxy_class=TestClientServerProxy)

    def testNotFoundResponse(self):
        self.assertRaises(BacklinkClientServerDoesNotExist,
                          self.pingback_client.ping,
                          '/non-existent-resource/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/good-source-document')

    def testErrorResponse(self):
        self.assertRaises(BacklinkClientRemoteError,
                          self.pingback_client.ping,
                          '/error/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/good-source-document')

    def testInvalidResponse(self):
        self.assertRaises(BacklinkClientError,
                          self.pingback_client.ping,
                          '/dummy/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/good-source-document')

    def testAlreadyRegisteredResponse(self):
        self.assertRaises(BacklinkClientAlreadyRegistered,
                          self.pingback_client.ping,
                          '/pingback/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/another-good-source-document/')

    def testSuccessfulPing(self):
        response = self.pingback_client.ping('/pingback/',
                                             'http://example.com/blog/pingable-entry/',
                                             'http://example.com/good-source-document/')
        self.assertTrue(response, 'Client did not return "True" for a successful ping')


class TrackBackClientTestCase(test.TestCase):
    fixtures = ['backlinks_test_data.json']
    urls = 'backlinks.tests.client_urls'

    def setUp(self):
        self.client = Client()
        self.trackback_client = TrackBackClient(url_opener=self.urlOpener)

    def urlOpener(self, url, data={}, headers={}):
        class Headers(object):
            def __init__(self, headers_dict):
                self.headers = headers_dict
            def getheader(self, name, default=None):
                normalized_name = name.upper().replace('-', '_')
                http_name = 'HTTP' + normalized_name
                return self.headers.get(normalized_name,
                                        self.headers.get(http_name, default))

        class ResponseWrapper(object):
            def __init__(self, response):
                self.headers = Headers(response)
                self.body = response.content
                self.charset = 'utf-8'
        response = self.client.post(url,
                                    urlencode(data),
                                    headers.get('Content-Type', None))
        if response.status_code != 200:
            raise HTTPError(url, response.status_code, 'Error', {}, None)
        return ResponseWrapper(response)

    def testNotFoundResponse(self):
        self.assertRaises(BacklinkClientServerDoesNotExist,
                          self.trackback_client.ping,
                          '/non-existent-resource/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/good-source-document')

    def testErrorResponse(self):
        self.assertRaises(BacklinkClientRemoteError,
                          self.trackback_client.ping,
                          '/error/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/good-source-document')

    def testInvalidResponse(self):
        self.assertRaises(BacklinkClientError,
                          self.trackback_client.ping,
                          '/dummy/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/good-source-document')

    def testTrackBackErrorResponse(self):
        self.assertRaises(BacklinkClientError,
                          self.trackback_client.ping,
                          '/trackback/0/',
                          'http://example.com/blog/pingable-entry/',
                          'http://example.com/another-good-source-document/')

    def testSuccessfulPing(self):
        response = self.trackback_client.ping('/trackback/1/',
                                              'http://example.com/blog/pingable-entry/',
                                              'http://example.com/good-source-document/')
        self.assertTrue(response, 'Client did not return "True" for a successful ping')

class BacklinksClientTestCase(test.TestCase):
    fixtures = ['backlinks_test_data.json']
    urls = 'backlinks.tests.client_urls'

    def setUp(self):
        self.backlinks_client = BacklinksClient()
    
    def testClientLoad(self):
        self.assertEquals(len(self.backlinks_client.clients),
                          2,
                          'BacklinksClient did not discover two protocol clients')
