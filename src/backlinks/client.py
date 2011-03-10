import sys
from urllib2 import URLError, HTTPError
from urlparse import urljoin

from django.core.urlresolvers import get_mod_func

from backlinks.conf import settings
from backlinks.utils import parse_external_links, url_reader, \
    get_site_absolute_uri, parse_title, parse_excerpt
from backlinks.models import OutboundBacklink
from backlinks.exceptions import BacklinkClientError


class BacklinksClient(object):
    """
    A client metaclass that can use all installed backlinks clients.

    """
    url_opener = url_reader.open

    def __init__(self, clients=None, url_opener=None):
        self._clients = clients
        self.url_opener = url_opener or self.url_opener

    def _get_clients(self):
        """
        Return a list of (protocol-name, display-name, client-object) tuples
        for all installed backlinks modules.

        """
        if not self._clients:
            self._clients = []
            for name, display, client_name in settings.INSTALLED_MODULES:
                try:
                    module_name, obj = get_mod_func(client_name)
                    mod = __import__(module_name)
                    client_module = sys.modules[module_name]
                    client = getattr(client_module, obj)
                except (ImportError, AttributeError):
                    continue
                if hasattr(client, 'autodiscover'):
                    self._clients.append((name, display, client))
        return self._clients
    clients = property(_get_clients)

    def discover_backlinks(self, markup):
        """
        Parse out links to all external resource in markup, autodiscover
        backlink servers for these resources, and return a list of
        (resource-url, ping-url, client-object, protocol-name) tuples.

        """
        links = parse_external_links(markup)
        ping_urls = []
        for link in links:
            ping_url = ''
            try:
                response = self.url_opener(link)
            except (URLError, HTTPError):
                # We ignore non-OK responses or connection errors
                continue
            for name, display, client in self.clients:
                ping_url = client.autodiscover(link, response)
                if ping_url:
                    ping_urls.append((response.url, ping_url, client, name))
                    break
            response.close()
        return ping_urls

    def register_successful_ping(self, target_url, source_url, protocol,
                                 source_object=None, title=None, excerpt=None):
        """
        Called for successful pings.
        Creates and saves a record of the ping using the ``OutboundBacklink``
        model.

        """
        ping_record, created = OutboundBacklink.objects.get_or_create(target_url=target_url,
                                                                      source_object=source_object)
        ping_record.status = OutboundBacklink.SUCCESSFUL_STATUS
        ping_record.protocol = protocol
        ping_record.source_url = source_url
        ping_record.target_url = target_url
        ping_record.title = title or ''
        ping_record.excerpt = excerpt or ''
        ping_record.save()
        return ping_record

    def register_unsuccessful_ping(self, target_url, source_url, protocol,
                                   source_object=None, title=None, excerpt=None):
        """
        Called for unsuccessful ping attempts.
        Creates and saves a record of the ping using the ``OutboundBacklink``
        model.

        """

        ping_record, created = OutboundBacklink.objects.get_or_create(target_url=target_url,
                                                                      source_object=source_object)
        ping_record.status = OutboundBacklink.UNSUCCESSFUL_STATUS
        ping_record.protocol = protocol
        ping_record.source_url = source_url
        ping_record.target_url = target_url
        ping_record.title = title or ''
        ping_record.excerpt = excerpt or ''
        ping_record.save()
        return ping_record

    def get_title(self, markup):
        """
        Return a title parsed from the given markup.

        """
        return parse_title(markup)

    def get_excerpt(self, markup, target_url):
        """
        Return a contextual excerpt parsed from the given markup.

        """
        return parse_excerpt(markup, target_url, settings.MAX_EXCERPT_WORDS)

    def get_url(self, model_instance):
        """
        Automatically determines the absolute URI for the given model_instance.

        """
        try:
            site_uri = get_site_absolute_uri()
            return urljoin(site_uri, model_instance.get_absolute_url())
        except AttributeError:
            raise ValueError('get_url must receive a model instance with a get_absolute_url method defined')

    def ping_all(self, markup, source_url=None, source_object=None, title=None, excerpt=None):
        """
        Ping all pingable, linked resources found in the given markup.

        """
        title = title or self.get_title(markup)
        if not source_url and source_object:
            source_url = self.get_url(source_object)
        for target_url, ping_url, client, client_name in self.discover_backlinks(markup):
            try:
                contextual_excerpt = excerpt or self.get_excerpt(markup, target_url)
                client.ping(ping_url, target_url, source_url,
                            title=title, excerpt=contextual_excerpt)
                self.register_successful_ping(target_url,
                                              source_url,
                                              client_name,
                                              source_object=source_object,
                                              title=title,
                                              excerpt=contextual_excerpt)
            except BacklinkClientError:
                self.register_unsuccessful_ping(target_url,
                                                source_url,
                                                client_name,
                                                source_object=source_object,
                                                title=title,
                                                excerpt=contextual_excerpt)
