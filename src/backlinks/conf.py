from django.conf import settings as project_settings
from backlinks import defaults as backlinks_defaults


class AppSettings(object):
    """
    An app-level settings container.

    """
    def __init__(self, defaults, overrides, prefix=None):
        self.defaults = defaults
        self.overrides = overrides
        if prefix:
            self.prefix = prefix + '_'
        else:
            self.prefix = ''
        self.attributes = {}
        
    def __getattr__(self, name):
        if name in self.attributes:
            return self.attributes[name]
        else:
            val = getattr(self.overrides,
                          self.prefix + name,
                          getattr(self.defaults, name))
            if callable(val):
                val = val()
            self.attributes[name] = val
        return val

settings = AppSettings(backlinks_defaults, project_settings, 'BACKLINKS')
