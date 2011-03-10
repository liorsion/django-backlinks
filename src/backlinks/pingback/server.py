import xmlrpclib
import urlparse

from django.http import HttpResponse, HttpResponseNotAllowed
from django.core.urlresolvers import resolve, Resolver404, \
    reverse, NoReverseMatch
from django.core.exceptions import ObjectDoesNotExist
from django.utils.functional import update_wrapper

from backlinks.server import BacklinksServer
from backlinks.exceptions import BacklinkServerError, BacklinkTargetDoesNotExist, \
    BacklinkTargetNotPingable, BacklinkSourceDoesNotExist
from backlinks.utils import get_site_absolute_uri

class PingbackServer(BacklinksServer):
    """
    A server implementation for the Pingback protocol.

    """
    protocol = 'pingback'
    csrf_exempt = True

    def __init__(self, path=None, absolute_uri=None):
        """
        Initialize the server with an optional path and absolute URI override.

        """
        self._path = path
        self._absolute_uri = absolute_uri
        self._view_registry = {}

    def get_path(self):
        """
        Determine the path at which the server is mounted.

        """
        if self._path:
            return self._path
        try:
            return reverse(self)
        except NoReverseMatch:
            return ''

    def get_absolute_uri(self, request=None):
        """
        Determine the server's absolute URI.

        """
        if self._absolute_uri:
            return urlparse.urljoin(self._absolute_uri, self.get_path())
        site_uri = get_site_absolute_uri(request)
        return urlparse.urljoin(site_uri, self.get_path())

    def add_view_to_registry(self, view, target_lookup, target_validator):
        """
        Add a view and its associated object lookup and validator to the
        server's registry.

        """
        self._view_registry[view] = (target_lookup, target_validator)

    def register_view(self, view, target_lookup, target_validator):
        """
        Register a view and its object lookup and validator, wrapping the
        view to provide autodiscovery headers when appropriate.

        """
        def wrapper(request, *args, **kwargs):
            response = view(request, *args, **kwargs)
            absolute_uri = self.get_absolute_uri(request)
            if absolute_uri:
                try:
                    target_uri = request.build_absolute_uri()
                    target_object = self.get_target_object(target_uri)
                    self.validate_target(target_uri, target_object)
                    response['X-Pingback'] = absolute_uri
                except BacklinkServerError:
                    pass
            return response
        wrapper = update_wrapper(wrapper, view)
        self.add_view_to_registry(wrapper, target_lookup, target_validator)
        return wrapper

    def lookup_view(self, target_uri):
        """
        Look up a view in the server's registry.

        """
        parsed_uri = urlparse.urlsplit(target_uri)
        try:
            view, args, kwargs = resolve(parsed_uri.path)
        except Resolver404:
            raise BacklinkTargetDoesNotExist
        return view, args, kwargs

    def get_target_object(self, target_uri, *args, **kwargs):
        """
        Look up a target object from an absolute URI.

        """
        view, args, kwargs = self.lookup_view(target_uri)
        try:
            target_lookup, target_validator = self._view_registry[view]
        except KeyError:
            raise BacklinkTargetNotPingable
        try:
            return target_lookup(*args, **kwargs)
        except ObjectDoesNotExist:
            raise BacklinkTargetDoesNotExist

    def validate_target(self, target_uri, target_object):
        """
        Validate a target object.

        """
        view, args, kwargs = self.lookup_view(target_uri)
        try:
            target_lookup, target_validator = self._view_registry[view]
            if not target_validator(target_uri, target_object):
                raise BacklinkTargetNotPingable
        except KeyError:
            raise BacklinkTargetNotPingable


    def xmlrpc_dispatch(self, request):
        """
        Perform XML-RPC (de)serialization of the request and called ping
        method.

        """
        try:
            params, method = xmlrpclib.loads(request.raw_post_data)
            if method != 'pingback.ping':
                raise Exception('Method "%s" not supported' % method)
            source_uri, target_uri = params
            response = self.register_ping(source_uri, target_uri)
            response = (response,)
            response = xmlrpclib.dumps(response, methodresponse=1,
                                       allow_none=0, encoding='utf-8')
        except xmlrpclib.Fault, fault:
            response = xmlrpclib.dumps(fault, allow_none=0, encoding='utf-8')
        except:
            import sys
            exc_type, exc_value, exc_tb = sys.exc_info()
            response = xmlrpclib.dumps(
                xmlrpclib.Fault(1, '%s:%s' % (exc_type, exc_value)),
                encoding='utf-8', allow_none=0,
                )
        return response

    def __call__(self, request):
        """
        Provides a Django view interface to the server.

        """
        if request.method != 'POST':
            return HttpResponseNotAllowed(['POST'])
        response = HttpResponse(mimetype='text/xml')
        response.write(self.xmlrpc_dispatch(request))
        response['Content-Length'] = str(len(response.content))
        return response

# A default server instance for convenience
default_server = PingbackServer()
