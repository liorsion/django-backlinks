import re
from StringIO import StringIO

from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseNotAllowed
from django.utils.xmlutils import SimplerXMLGenerator

from backlinks.exceptions import BacklinkServerError,\
    BacklinkTargetDoesNotExist, BacklinkTargetNotPingable
from backlinks.utils import get_site_absolute_uri
from backlinks.server import BacklinksServer

CONTENT_TYPE_RE = re.compile(r'application/x-www-form-urlencoded')

class TrackBackResponse(HttpResponse):
    """
    A response object that generates the appropriate TrackBack
    response document.

    """
    def __init__(self, error_message=None, content='', mimetype=None,
                    status=None, content_type='text/xml; charset=utf-8'):
        super(TrackBackResponse, self).__init__(content=content,
                                                mimetype=mimetype,
                                                status=status,
                                                content_type=content_type)
        response_content = StringIO()
        generator = SimplerXMLGenerator(response_content, 'utf-8')
        generator.startDocument()
        generator.startElement('response', {})
        if error_message:
            generator.addQuickElement('error', '1')
            generator.addQuickElement('message', error_message)
        else:
            generator.addQuickElement('error', '0')
        generator.endElement('response')
        self.content = response_content.getvalue()
        response_content.close()
        self['Content-Length'] = str(len(self.content))


class TrackBackServer(BacklinksServer):
    """
    A server implementation for the TrackBack protocol.

    """
    protocol = 'trackback'
    csrf_exempt = True

    def __init__(self, target_lookup, target_validator):
        super(TrackBackServer, self).__init__()
        self._target_lookup = target_lookup
        self._target_validator = target_validator

    def validate_content_type(self, request):
        """
        Validate that the request uses the correct Content-Type.

        """
        content_type = request.META.get('CONTENT_TYPE', '')
        if not CONTENT_TYPE_RE.search(content_type):
            raise BacklinkServerError('Invalid Content-Type')
        return content_type

    def get_target_object(self, target_uri, *args, **kwargs):
        """
        Get the target object using the ``target_lookup`` function.

        """
        try:
            return self._target_lookup(*args, **kwargs)
        except ObjectDoesNotExist:
            raise BacklinkTargetDoesNotExist

    def validate_target(self, target_uri, target_object):
        """
        Validate the target object using the ``target_validator``
        function.

        """
        if self._target_validator(target_uri, target_object):
            return True
        raise BacklinkTargetNotPingable

    def __call__(self, request, *args, **kwargs):
        """
        The Django view interface for the server.

        """
        try:
            if not request.method == 'POST':
                return HttpResponseNotAllowed(['POST'])
            self.validate_content_type(request)
            target_object = self.get_target_object(None, *args, **kwargs)
            response = self.register_ping(request.POST.get('url', ''),
                                          None, target_object,
                                          request.POST.get('title'),
                                          request.POST.get('excerpt')
                                          )
            return TrackBackResponse()
        except BacklinkServerError, e:
            return TrackBackResponse(e.message)
