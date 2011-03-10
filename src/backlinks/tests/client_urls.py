from xmlrpclib import Fault
from SimpleXMLRPCServer import SimpleXMLRPCDispatcher

from django.conf.urls.defaults import *
from django.http import HttpResponse, HttpResponseServerError, HttpResponseNotFound, HttpResponseNotAllowed, Http404

mock_responses = {
    ('http://example.com/another-good-source-document/', 'http://example.com/blog/pingable-entry/'): Fault(48, 'Ping already registered'),
    ('http://example.com/good-source-document/', 'http://example.com/blog/pingable-entry/'): 'Ping registered'
}

def mock_ping(sourceURI, targetURI):
    response = mock_responses.get((sourceURI, targetURI), Fault(0, 'Error'))
    if isinstance(response, Fault):
        raise response
    return response


try:
    dispatcher = SimpleXMLRPCDispatcher()
except TypeError:
    dispatcher = SimpleXMLRPCDispatcher(allow_none=False, encoding=None)

dispatcher.register_function(mock_ping, "pingback.ping")

def mock_pingback_server(request):
    if not request.method == 'POST':
        return HttpResponseNotAllowed(['POST'])
    response = HttpResponse(mimetype='text/xml')
    response.write(dispatcher._marshaled_dispatch(request.raw_post_data))
    response['Content-Length'] = str(len(response.content))
    return response

TRACKBACK_SUCCESS_RESPONSE = '<?xml version="1.0" encoding="utf-8"?><response><error>0</error></response>'
TRACKBACK_FAILURE_RESPONSE = '<?xml version="1.0" encoding="utf-8"?><response><error>1</error><message>An error occurred</message></response>'

def mock_trackback_server(request, id):
    try:
        id = int(id)
    except ValueError:
        raise Http404
    if id == 1:
        return HttpResponse(TRACKBACK_SUCCESS_RESPONSE, mimetype='text/xml')
    return HttpResponse(TRACKBACK_FAILURE_RESPONSE, mimetype='text/xml')

urlpatterns = patterns('',
    url(r'^pingback/$', mock_pingback_server, name='pingback-server'),
    url(r'^trackback/(\d+)/$', mock_trackback_server, name='trackback-server'),
    url(r'^error/$', lambda request: HttpResponseServerError('error'), name='server-error'),
    url(r'^dummy/$', lambda request: HttpResponse('a response'), name='dummy'),
)

handler500 = 'backlinks.tests.client_urls.handle_500'
handler404 = 'backlinks.tests.client_urls.handle_404'

def handle_500(request):
    return HttpResponseServerError('error')

def handle_404(request):
    return HttpResponseNotFound('not found')
