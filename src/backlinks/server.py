import re
import urllib2
from urlparse import urljoin

try:
    from django.forms.fields import url_re
except ImportError:
    from django.core.validators import URLValidator
    url_re = URLValidator.regex
from django.contrib.contenttypes.models import ContentType

from backlinks.exceptions import BacklinkServerError, \
    BacklinkTargetDoesNotExist, BacklinkSourceDoesNotExist, \
    BacklinkSourceDoesNotLink, BacklinkAlreadyRegistered
from backlinks.models import InboundBacklink
from backlinks.conf import settings
from backlinks.utils import get_site_absolute_uri, url_reader, \
    document_has_target_link, parse_title, parse_excerpt


INVALID_SOURCE_CONTENT_TYPE_RE = re.compile('(audio|image|video|model)', re.IGNORECASE)

class BacklinksServer(object):
    """
    A base server class for implementing backlink protocol servers.
    Provides methods necessary to validate and record ping requests.

    """
    url_reader = url_reader
    protocol = ''

    def __init__(self):
        super(BacklinksServer, self).__init__()

    def validate_uri(self, uri):
        """
        Ensure the given string is an absolute URI.

        """
        if not url_re.search(uri):
            raise BacklinkServerError

    def validate_target_uri(self, target_uri):
        """
        Validate that the given target URI is well-formed and appears to
        point to a resource we know about.

        """
        try:
            self.validate_uri(target_uri)
        except BacklinkServerError:
            raise BacklinkTargetDoesNotExist

        if not target_uri.startswith(get_site_absolute_uri()):
            raise BacklinkServerTargetDoesNotExist

    def validate_source_uri(self, source_uri):
        """
        Validate that the given source URI is well-formed.

        """
        try:
            self.validate_uri(source_uri)
        except BacklinkServerError:
            raise BacklinkSourceDoesNotExist

    def get_target_uri(self, target_object):
        """
        Return an absolute URI for a given target Django model instance.

        """
        site_uri = get_site_absolute_uri()
        try:
            path = target_object.get_absolute_url()
        except AttributeError:
            return ''
        return urljoin(site_uri, path)

    def get_target_object(self, target_uri, *args, **kwargs):
        """
        Retrieve a target object given its URI and/or any additional
        arguments.
        Subclasses must override this.

        """
        raise NotImplementedError

    def validate_target(self, target_uri, target_object):
        """
        Ensure that the given target is a pingable resource.
        Subclasses must override this.

        """
        raise NotImplementedError

    def validate_unregistered(self, source_uri, target_uri, target_object):
        """
        Ensure a ping with the given parameters has not been registered.

        """
        target_content_type = None
        try:
            target_content_type = ContentType.objects.get_for_model(target_object)
        except (AttributeError, ContentType.DoesNotExist):
            pass
        try:
            if target_content_type:
                backlink = InboundBacklink.objects.get(source_url=source_uri,
                                                       target_url=target_uri,
                                                       content_type=target_content_type,
                                                       object_id=target_object.pk)
            else:
                backlink = InboundBacklink.objects.get(source_url=source_uri,
                                                       target_url=target_uri)
            raise BacklinkAlreadyRegistered
        except InboundBacklink.DoesNotExist:
            pass

    def get_source(self, source_uri):
        """
        Retrieve and return a handle to the given source resource.

        """
        try:
            return self.url_reader.open(source_uri)
        except urllib2.HTTPError, e:
            if e.code == 404:
                raise BacklinkSourceDoesNotExist
            raise BacklinkServerError('Could not connect to given source')
        except (urllib2.URLError, IOError):
            raise BacklinkServerError

    def validate_source_is_markup(self, source):
        """
        Ensure the resource is a valid markup type.

        """
        content_type = source.headers.getheader('content-type', None)
        if not content_type or INVALID_SOURCE_CONTENT_TYPE_RE.search(content_type):
            raise BacklinkServerError('Invalid Content-Type')

    def validate_source_links(self, source, target_uri):
        """
        Ensure the source markup document links to the target resource.

        """
        if not document_has_target_link(source.body, target_uri):
            raise BacklinkSourceDoesNotLink

    def validate_source(self, source, target_uri):
        """
        Ensure that the source document is valid.

        """
        self.validate_source_is_markup(source)
        self.validate_source_links(source, target_uri)

    def get_title(self, markup, charset=None):
        """
        Return a title parsed from the given markup.

        """
        return parse_title(markup, charset)

    def get_excerpt(self, markup, target_url, charset=None):
        """
        Return a contextual excerpt parsed from the given markup.

        """
        return parse_excerpt(markup, target_url, settings.MAX_EXCERPT_WORDS, charset)

    def record_successful_ping(self, source_uri, target_uri,
                               target_object=None,
                               title='', excerpt=''):
        """
        Record a successful ping attempt.

        """
        backlink = InboundBacklink()
        backlink.source_url = source_uri
        backlink.target_url = target_uri
        backlink.title = title
        backlink.excerpt = excerpt
        backlink.protocol = self.protocol
        backlink.target_object = target_object
        backlink.save()

    def record_unsuccessful_ping(self, source_uri, target_uri,
                                 target_object=None,
                                 title='', excerpt='', reason=''):
        """
        Record an unsuccessful ping attempt.

        """
        pass

    def register_ping(self, source_uri, target_uri=None, target_object=None,
                      title='', excerpt=''):
        """
        Validate ping parameters and record the attempt.

        """
        try:
            self.validate_source_uri(source_uri)
            if not target_uri and not target_object:
                raise BacklinkServerTargetDoesNotExist
            elif target_uri and not target_object:
                self.validate_target_uri(target_uri)
                target_object = self.get_target_object(target_uri)
            else:
                target_uri = self.get_target_uri(target_object)
            self.validate_target(target_uri, target_object)
            self.validate_unregistered(source_uri, target_uri, target_object)
            source = self.get_source(source_uri)
            self.validate_source(source, target_uri)
            if not title:
                title = self.get_title(source.body, source.charset)
            if not excerpt:
                excerpt = self.get_excerpt(source.body, target_uri, source.charset)
            self.record_successful_ping(source_uri,
                                        target_uri, target_object,
                                        title, excerpt)
            return 'Ping from %s to %s registered' % (source_uri, target_uri)
        except BacklinkServerError, e:
            self.record_unsuccessful_ping(source_uri,
                                          target_uri or '', target_object,
                                          title or '', excerpt or '', e.message)
            raise
        
    def __call__(self, request, *args, **kwargs):
        """
        Subclasses must override this to provide Django view behavior.

        """
        raise NotImplementedError
