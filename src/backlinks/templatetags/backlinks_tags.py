from django.template import Library, Node, Variable, TemplateSyntaxError
from django.contrib.contenttypes.models import ContentType
from backlinks.models import InboundLinkback

register = Library()

class BacklinkListObject(Node):
    def __init__(self, target_object_name, template_var_name=None):
        self.target_object = Variable(target_object_name)
        self.template_var_name = template_var_name or 'backlinks'

    def render(self, context):
        try:
            target_object = self.target_object.resolve(context)
            content_type = ContentType.objects.get_for_model(target_object)
            pings = InboundLinkback.objects.approved().filter(content_type=content_type, \
                            object_id=target_object.id)
            context[self.template_var_name] = pings
        except:
            pass
        return ''

def do_ping_list(parser, token):
    var_name = None
    bits = token.split_contents()
    bits_len = len(bits)
    if bits_len not in (2, 4):
        raise TemplateSyntaxError("%s tag accepts only one or three arguments" % bits[0])
    target_object_name = bits[1]
    if bits_len == 4:
        if bits[2] == 'as':
            var_name = bits[3]
        else:
            raise TemplateSyntaxError("second argument to %s tag must be 'as <variable_name>'" % bits[0])
    return BacklinkListObject(target_object_name, var_name)


register.tag('backlinks_for_model', do_ping_list)
