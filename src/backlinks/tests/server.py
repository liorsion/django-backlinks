import re
from xmlrpclib import Fault, loads
from urllib import urlencode

from django import test
from django.test.client import Client
from django import template

from backlinks.models import InboundBacklink
from backlinks.tests.xmlrpc import TestClientServerProxy

TRACKBACK_CONTENT_TYPE = 'application/x-www-form-urlencoded; charset=utf-8'

class PingbackServerTestCase(test.TestCase):
    fixtures = ['backlinks_test_data.json']
    urls = 'backlinks.tests.server_urls'

    def setUp(self):
        self.client = Client(SERVER_NAME='example.com')
        self.xmlrpc_client = TestClientServerProxy('/pingback/')

    def testDiscoverPath(self):
        from backlinks.tests.server_urls import mock_pingback_server
        self.assertEquals(mock_pingback_server.get_path(),
                          '/pingback/',
                          'Server did not correctly determine mount path')

    def testDiscoverAbsoluteURI(self):
        from backlinks.tests.server_urls import mock_pingback_server
        self.assertEquals(mock_pingback_server.get_absolute_uri(),
                          'http://example.com/pingback/',
                          'Server did not correctly determine its URI')

    def testPathOverride(self):
        from backlinks.pingback.server import PingbackServer
        server = PingbackServer(path='/ping-back/')
        self.assertEquals(server.get_path(),
                          '/ping-back/',
                          'Server did not correctly set path from override')

    def testAbsoluteURIOverride(self):
        from backlinks.pingback.server import PingbackServer
        server = PingbackServer(absolute_uri='http://djangoproject.com/ping-back/')
        self.assertEquals(server.get_absolute_uri(),
                          'http://djangoproject.com/ping-back/',
                          'Server did not correctly set absolute URI from override')

    def testDisallowedMethod(self):
        response = self.client.get('/pingback/')
        self.assertEquals(response.status_code,
                          405,
                          'Server returned incorrect status code for disallowed HTTP method')

    def testNonExistentRPCMethod(self):
        self.assertRaises(Fault, self.xmlrpc_client.foo)

    def testBadPostData(self):
        post_data = urlencode({'sourceURI': 'http://example.com/good-source-document/',
                               'targetURI': 'http://example.com/blog/pingable-entry/'})
        response = self.client.post('/pingback/', post_data, TRACKBACK_CONTENT_TYPE)
        self.assertRaises(Fault,
                          loads,
                          response.content)
        


    def testPingbackResponseHeader(self):
        response = self.client.get('/blog/pingable-entry/')
        self.assertTrue(bool(response.get('X-Pingback', False)),
                        'Server did not add X-Pingback response header for '
                        'registered view representing a pingable resource')
        response = self.client.get('/blog/non-pingable-entry/')
        self.assertFalse(response.get('X-Pingback', False),
                         'Server incorrectly added X-Pingback response header for '
                         'registered view representing a non-pingable resource')

    def testPingNonExistentTargetURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/blog/non-existent-resource/',
                          'http://example.com/blog/non-existent-resource')
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/blog/non-existent-resource/',
                                             'http://example.com/blog/non-existent-resource')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              32,
                              'Server did not return "target does not exist" error')
        
    def testPingNonPingableTargetURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/blog/non-existent-resource/',
                          'http://example.com/blog/non-pingable-entry/')
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/blog/non-existent-resource/',
                                             'http://example.com/blog/non-pingable-entry/')
        except Fault, f:
            self.assertEquals(f.faultCode, 
                              33,
                              'Server did not return "target not pingable" error')

    def testPingNonExistentSourceURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/non-existent-resource/',
                          'http://example.com/blog/pingable-entry/')
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/non-existent-resource/',
                                             'http://example.com/blog/pingable-entry/')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              16,
                              'Server did not return "source does not exist" error')

    def testPingSourceURIServerError(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/server-error/',
                          'http://example.com/blog/pingable-entry/')
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/server-error/',
                                             'http://example.com/blog/pingable-entry/')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              0,
                              'Server did not return "generic error" response')

    def testPingNonLinkingSourceURI(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/bad-source-document/',
                          'http://example.com/blog/pingable-entry/')
        
        try:
            self.xmlrpc_client.pingback.ping('http://example.com/bad-source-document/',
                                             'http://example.com/blog/pingable-entry/')
        except Fault, f:
            self.assertEquals(f.faultCode,
                              17,
                              'Server did not return "source URI does not link" response')

    def testPingSourceURILinks(self):
        r = self.xmlrpc_client.pingback.ping('http://example.com/good-source-document/',
                                             'http://example.com/blog/pingable-entry/')
        registered_ping = InboundBacklink.objects.get(source_url='http://example.com/good-source-document/',
                                                      target_url='http://example.com/blog/pingable-entry/')
        
    def testPingAlreadyRegistered(self):
        self.assertRaises(Fault,
                          self.xmlrpc_client.pingback.ping,
                          'http://example.com/another-good-source-document/',
                          'http://example.com/blog/pingable-entry/')

        try:
            self.xmlrpc_client.pingback.ping('http://example.com/another-good-source-document/',
                                             'http://example.com/blog/pingable-entry/')
        except Fault, f:
            self.assertEqual(f.faultCode,
                             48,
                             'Server did not return "ping already registered" error')

    def testPingbackLinkTemplateTag(self):
        t = template.Template("{% load pingback_tags %}{% pingback_link pingback_path %}")
        c = template.Context({'pingback_path': '/pingback/'})
        rendered = t.render(c)
        link_re = re.compile(r'<link rel="pingback" href="([^"]+)" ?/?>')
        match = link_re.search(rendered)
        self.assertTrue(bool(match), 'Pingback link tag did not render')
        self.assertEquals(match.groups(0)[0], 'http://example.com/pingback/',
                          'Pingback link tag rendered incorrectly')


class TrackBackServerTestCase(test.TestCase):
    fixtures = ['backlinks_test_data.json']
    urls = 'backlinks.tests.server_urls'

    def setUp(self):
        self.client = Client()

    def trackbackPOSTRequest(self, path, params):
        return self.client.post(path, urlencode(params), content_type=TRACKBACK_CONTENT_TYPE)

    def assertTrackBackErrorResponse(self, response, msg):
        if response.content.find('<error>1</error>') == -1:
            raise self.failureException, msg

    def testDisallowedMethod(self):
        response = self.client.get('/trackback/blog/pingable-entry/')
        self.assertEquals(response.status_code,
                          405,
                          'Server returned incorrect status code for disallowed HTTP method')

    def testPingInvalidContentType(self):
        params = {'url': 'http://example.com/good-source-document/'}
        response = self.client.post('/trackback/blog/pingable-entry/',
                                    params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping with invalid Content-Type')
                                    

    def testPingNoURLParameter(self):
        params = {'title': 'Example', 'excerpt': 'Example'}
        response = self.trackbackPOSTRequest('/trackback/blog/pingable-entry/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response'
                                          'for ping with no URL parameter')

    def testPingBadURLParameter(self):
        params = {'url': 'bad url'}
        response = self.trackbackPOSTRequest('/trackback/blog/pingable-entry/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping with bad URL parameter')

    def testPingNonExistentTarget(self):
        params = {'url': 'http://example.com/good-source-document/'}
        response = self.trackbackPOSTRequest('/trackback/blog/non-existent-resource/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping against non-existent resource')

    def testPingNonPingableTarget(self):
        params = {'url': 'http://example.com/good-source-document/'}
        response = self.trackbackPOSTRequest('/trackback/blog/non-pingable-entry/',
                                             params)
        self.assertTrackBackErrorResponse(response,
                                          'Server did not return error response for ping against non-pingable resource')

    def testPingSuccess(self):
        title = 'Backlinks Test - Test Good Source Document'
        excerpt = 'This is a summary of the good source document'
        params = {'url': 'http://example.com/good-source-document/', 'title': title, 'excerpt': excerpt}
        response = self.trackbackPOSTRequest('/trackback/blog/pingable-entry/',
                                             params)
        self.assertTrue(response.content.find('<error>0</error>') > -1,
                        'Server did not return success response for a valid ping request')
        registered_ping = InboundBacklink.objects.get(source_url='http://example.com/good-source-document/',
                                                      target_url='http://example.com/blog/pingable-entry/')
        self.assertEquals(registered_ping.title,
                          title,
                          'Server did not use title from ping request when registering')
        self.assertEquals(registered_ping.excerpt,
                          excerpt,
                          'Server did not use excerpt from ping request when registering')

    def testTrackBackRDFTemplateTag(self):
        t = template.Template("{% load trackback_tags %}{% trackback_rdf object_url object_title trackback_url True %}")
        c = template.Context({'trackback_url': '/trackback/blog/pingable-entry/',
                              'object_url': '/blog/pingable-entry/',
                              'object_title': 'Pingable Test Entry'})
        rendered = t.render(c)
        link_re = re.compile(r'dc:identifier="(?P<link>[^"]+)"')
        match = link_re.search(rendered)
        self.assertTrue(bool(match), 'TrackBack RDF not rendered')
        self.assertEquals(match.groups('link')[0], 'http://example.com/blog/pingable-entry/',
                          'TrackBack RDF did not contain a valid target URI')
        ping_re = re.compile(r'trackback:ping="(?P<link>[^"]+)"')
        match = ping_re.search(rendered)
        self.assertTrue(bool(match), 'TrackBack RDF not rendered')
        self.assertEquals(match.groups('link')[0], 'http://example.com/trackback/blog/pingable-entry/',
                          'TrackBack RDF did not contain a TrackBack server URI')
