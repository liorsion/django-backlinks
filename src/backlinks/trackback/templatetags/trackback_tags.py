import urlparse

from django import template
from django.template.loader import get_template
from django.utils.translation import ugettext_lazy as _
from django.conf import settings

from backlinks.utils import get_site_absolute_uri

register = template.Library()

class TrackbackRDFNode(template.Node):
    def __init__(self, object_url, object_title, trackback_url, with_comments=True):
        self.object_url = template.Variable(object_url)
        self.object_title = template.Variable(object_title)
        self.trackback_url = template.Variable(trackback_url)
        self.with_comments = with_comments

    def render(self, context):
        rdf = ''
        try:
            site_uri = get_site_absolute_uri()
            if not site_uri:
                request_obj = template.Variable('request').resolve(context)
                try:
                    site_uri = get_site_absolute_uri(request_obj)
                except AttributeError:
                    return ''
            object_url = self.object_url.resolve(context)
            if not object_url.lower().startswith('http'):
                path = object_url
                object_url = urlparse.urljoin(site_uri, object_url)
            object_title = self.object_title.resolve(context)
            trackback_url = self.trackback_url.resolve(context)
            if not trackback_url.lower().startswith('http'):
                scheme, netloc, path, query, fragment = urlparse.urlsplit(object_url, 'http')
                path = trackback_url
                trackback_url = urlparse.urlunsplit((scheme, netloc, path, None, None))
            t = get_template('backlinks/trackback/rdf.xml')
            c = template.Context({'url': object_url, 'title': object_title, 'trackback_url': trackback_url})
            rdf = t.render(c)
            if self.with_comments:
                rdf = u'<!-- %s -->' % rdf
        except template.VariableDoesNotExist:
            pass
        return rdf

def do_trackback_rdf(parser, token):
    try:
        tag_name, object_url, object_title, trackback_url, with_comments = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(_('%s tag requires exactly four arguments') % token.split_contents()[0])
    if with_comments not in ('True', 'False'):
        raise template.TemplateSyntaxError(_('The last argument to %s must be either True or False') % tag_name)
    if with_comments == 'True':
        with_comments = True
    else:
        with_comments = False
    return TrackbackRDFNode(object_url, object_title, trackback_url, with_comments)

register.tag('trackback_rdf', do_trackback_rdf)
