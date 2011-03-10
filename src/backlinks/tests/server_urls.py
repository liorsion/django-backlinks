from django.conf.urls.defaults import *
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, Http404

from backlinks.tests.mock import mock_reader, available_entries
from backlinks.pingback.server import PingbackServer
from backlinks.trackback.server import TrackBackServer

# Mock server classes

class MockPingbackServer(PingbackServer):
    url_reader = mock_reader

mock_pingback_server = MockPingbackServer()

class MockTrackBackServer(TrackBackServer):
    url_reader = mock_reader

# Mock target getter and validator

def get_entry_from_slug(slug=None):
    if slug and slug in available_entries:
        return available_entries[slug]
    raise ObjectDoesNotExist

entry_is_pingable = lambda uri, obj: obj.is_pingable

# Mock target view

def entry_detail(request, slug=None):
    try:
        entry = get_entry_from_slug(slug)
    except ObjectDoesNotExist:
        raise Http404
    return HttpResponse(entry.content)

entry_detail = mock_pingback_server.register_view(entry_detail,
                                                  get_entry_from_slug,
                                                  entry_is_pingable)

urlpatterns = patterns('',
    url(r'^blog/(?P<slug>[\w-]+)/$',
        entry_detail,
        name='entry-detail'),
    url(r'^pingback/$',
        mock_pingback_server,
        name='pingback-server'),
    url(r'^trackback/blog/(?P<slug>[\w-]+)/$',
        MockTrackBackServer(get_entry_from_slug, entry_is_pingable),
        name='trackback-server'),
)
