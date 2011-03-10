import datetime

from django.db import models
from django.core.exceptions import ObjectDoesNotExist
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes import generic
from django.contrib.contenttypes.models import ContentType

from backlinks.managers import InboundBacklinkManager

class InboundBacklink(models.Model):
    """
    A record of a link from an external resource to an internal resource.

    """
    APPROVED_STATUS = 1
    UNAPPROVED_STATUS = 2

    STATUS_CHOICES = (
        (APPROVED_STATUS, _('approved')),
        (UNAPPROVED_STATUS, _('unapproved')),
    )

    source_url = models.URLField(_('linking resource identifier'))
    target_url = models.URLField(_('linked resource identifier'), verify_exists=False)
    received = models.DateTimeField(_('received'), default=datetime.datetime.now)
    title = models.CharField(_('title of linking resource'), max_length=1024, blank=True)
    excerpt = models.TextField(_('excerpt from linking resource'), blank=True)
    status = models.PositiveIntegerField(_('status'), choices=STATUS_CHOICES, default=UNAPPROVED_STATUS)
    protocol = models.CharField(_('protocol'), max_length=32, blank=True)

    # Target object
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    target_object = generic.GenericForeignKey('content_type', 'object_id')

    objects = InboundBacklinkManager()

    class Meta:
        verbose_name = _('inbound backlink')
        verbose_name_plural = _('inbound backlinks')
        ordering = ['-received']
        get_latest_by = 'received'


    def __unicode__(self):
        return _('Inbound backlink from %s to %s') % (self.source_uri, self.target_object or self.target_uri)


class OutboundBacklink(models.Model):
    """
    A record of a link from an internal resource to an external resource.

    """
    PENDING_STATUS = 1
    SUCCESSFUL_STATUS = 2
    UNSUCCESSFUL_STATUS = 3

    STATUS_CHOICES = (
        (PENDING_STATUS, _('pending')),
        (SUCCESSFUL_STATUS, _('successful')),
        (UNSUCCESSFUL_STATUS, _('unsuccessful')),
    )

    target_url = models.URLField(_('linked resource'))
    source_url = models.URLField(_('linking resource'))
    sent = models.DateTimeField(_('sent'), default=datetime.datetime.now)
    title = models.CharField(_('sent title'), max_length=1024, blank=True)
    excerpt = models.TextField(_('sent excerpt'))
    protocol = models.CharField(_('protocol'), max_length=32, blank=True)
    status = models.PositiveIntegerField(_('status'), choices=STATUS_CHOICES)
    message = models.CharField(_('server response message'), max_length=1024, blank=True)

    # Source object
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    source_object = generic.GenericForeignKey('content_type', 'object_id')

    def __unicode__(self):
        return _('Outbound backlink from %s to %s') % (self.source_object or self.source_uri, self.target_uri)

    def increment_attempts(self):
        self.num_attempts = self.num_attempts + 1
