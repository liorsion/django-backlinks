import urllib
import urlparse

from django.contrib.sites.models import Site, RequestSite

from backlinks.utils.unicodifier import unicodify
from backlinks.utils.urlreader import ResponseWrapper, URLReader
from backlinks.utils.parsers import HttpLinkParser, TitleParser, \
    ContextualExcerptParser
from backlinks.conf import settings

def get_site_absolute_uri(request=None):
    if Site._meta.installed:
        domain = Site.objects.get_current().domain
    elif request:
        domain = RequestSite(request).domain
    else:
        return ''
    scheme, uri = urllib.splittype(domain)
    if scheme not in ('http', 'https'):
        domain = 'http://' + domain
    scheme, domain, path, querystring, fragment = urlparse.urlsplit(domain)
    return urlparse.urlunsplit((scheme, domain, path, None, None))

class LimitedResponseWrapper(ResponseWrapper):
    def read(self, max_length=settings.MAX_URL_READ_LENGTH):
        return super(LimitedResponseWrapper, self).read(max_length)

class LimitedURLReader(URLReader):
    RESPONSE_CLASS = LimitedResponseWrapper

url_reader = LimitedURLReader({'User-Agent': settings.USER_AGENT_STRING,})

def parse_external_links(document):
    parser = HttpLinkParser()
    links = parser.parse(document)
    site_uri = get_site_absolute_uri()
    return [link for link in links if not link.startswith(site_uri)]

def document_has_target_link(markup, target_link):
    links = HttpLinkParser().parse(markup)
    return target_link in links

def parse_title(markup, charset=None):
    parser = TitleParser()
    try:
        title = parser.parse(markup)
        converted, original_encoding = unicodify(markup, [charset] or [])
        return converted
    except:
        return ''

def parse_excerpt(markup, target_url, max_words, charset=None):
    parser = ContextualExcerptParser()
    try:
        found_excerpts = parser.parse(markup, max_words)
    except:
        return ''
    if found_excerpts:
         excerpt = found_excerpts[0]
         converted, original_encoding = unicodify(excerpt, [charset] or [])
         return converted
    return ''
