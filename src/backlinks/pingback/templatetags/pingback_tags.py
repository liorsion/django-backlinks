from urlparse import urljoin

from django import template
from django.utils.translation import ugettext_lazy as _

from backlinks.utils import get_site_absolute_uri

register = template.Library()

PINGBACK_LINK_TAG = '<link rel="pingback" href="%s"'

class PingbackLinkTagNode(template.Node):
    def __init__(self, pingback_path, xhtml):
        self.pingback_path = template.Variable(pingback_path)
        self.xhtml = xhtml

    def render(self, context):
        try:
            pingback_path = self.pingback_path.resolve(context)
            site_uri = get_site_absolute_uri()
            if not site_uri:
                request_obj = template.Variable('request').resolve(context)
                if hasattr(request_obj, 'get_host'):
                    site_uri = get_site_absolute_uri(request_obj)
                else:
                    return ''
            pingback_absolute_uri = urljoin(site_uri, pingback_path)
            tag_start = PINGBACK_LINK_TAG % pingback_absolute_uri
            if not self.xhtml:
                return tag_start + '>'
            else:
                return tag_start + ' />'
        except template.VariableDoesNotExist:
            return ''

def do_pingback_link_tag(parser, token):
    parts = token.split_contents()
    num_parts = len(parts)
    tag_name = parts[0]
    if num_parts not in (2, 3):
        raise template.TemplateSyntaxError(_('%s tag requires either one or two arguments') % tag_name)
    pingback_path = parts[1]
    if num_parts == 3:
        if not parts[2] in ('True', 'False'):
            raise template.TemplateSyntaxError(_('The second argument to %s must be either True or False') % tag_name)
        if parts[2] == 'True':
            xhtml = True
        else:
            xhtml = False
    else:
        xhtml = False
    return PingbackLinkTagNode(pingback_path, xhtml)

register.tag('pingback_link', do_pingback_link_tag)
