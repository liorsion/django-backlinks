import unittest

from backlinks.tests.server import PingbackServerTestCase, TrackBackServerTestCase
from backlinks.tests.client import PingbackClientTestCase, TrackBackClientTestCase, \
    BacklinksClientTestCase

def suite():
    suite = unittest.TestSuite()
    # Pingback Server Tests
    suite.addTest(PingbackServerTestCase('testDiscoverPath'))
    suite.addTest(PingbackServerTestCase('testDiscoverAbsoluteURI'))
    suite.addTest(PingbackServerTestCase('testPathOverride'))
    suite.addTest(PingbackServerTestCase('testAbsoluteURIOverride'))
    suite.addTest(PingbackServerTestCase('testDisallowedMethod'))
    suite.addTest(PingbackServerTestCase('testNonExistentRPCMethod'))
    suite.addTest(PingbackServerTestCase('testBadPostData'))
    suite.addTest(PingbackServerTestCase('testPingbackResponseHeader'))
    suite.addTest(PingbackServerTestCase('testPingNonExistentTargetURI'))
    suite.addTest(PingbackServerTestCase('testPingNonPingableTargetURI'))
    suite.addTest(PingbackServerTestCase('testPingNonExistentSourceURI'))
    suite.addTest(PingbackServerTestCase('testPingSourceURIServerError'))
    suite.addTest(PingbackServerTestCase('testPingNonLinkingSourceURI'))
    suite.addTest(PingbackServerTestCase('testPingSourceURILinks'))
    suite.addTest(PingbackServerTestCase('testPingAlreadyRegistered'))
    suite.addTest(PingbackServerTestCase('testPingbackLinkTemplateTag'))
    # TrackBack Server Tests
    suite.addTest(TrackBackServerTestCase('testDisallowedMethod'))
    suite.addTest(TrackBackServerTestCase('testPingInvalidContentType'))
    suite.addTest(TrackBackServerTestCase('testPingNoURLParameter'))
    suite.addTest(TrackBackServerTestCase('testPingBadURLParameter'))
    suite.addTest(TrackBackServerTestCase('testPingNonExistentTarget'))
    suite.addTest(TrackBackServerTestCase('testPingNonPingableTarget'))
    suite.addTest(TrackBackServerTestCase('testPingSuccess'))
    suite.addTest(TrackBackServerTestCase('testTrackBackRDFTemplateTag'))
    # Pingback Client Tests
    suite.addTest(PingbackClientTestCase('testNotFoundResponse'))
    suite.addTest(PingbackClientTestCase('testErrorResponse'))
    suite.addTest(PingbackClientTestCase('testInvalidResponse'))
    suite.addTest(PingbackClientTestCase('testAlreadyRegisteredResponse'))
    suite.addTest(PingbackClientTestCase('testSuccessfulPing'))
    # TrackBack Client Tests
    suite.addTest(TrackBackClientTestCase('testNotFoundResponse'))
    suite.addTest(TrackBackClientTestCase('testErrorResponse'))
    suite.addTest(TrackBackClientTestCase('testInvalidResponse'))
    suite.addTest(TrackBackClientTestCase('testTrackBackErrorResponse'))
    suite.addTest(TrackBackClientTestCase('testSuccessfulPing'))
    # BacklinksClient Tests
    suite.addTest(BacklinksClientTestCase('testClientLoad'))
    return suite
    
