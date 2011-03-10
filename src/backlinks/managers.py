from django.db import models
from django.contrib.contenttypes.models import ContentType

class InboundBacklinkManager(models.Manager):
    def approved(self):
        return self.get_query_set().filter(status__exact=self.model.APPROVED_STATUS)

    def for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_id=model._get_pk_val())
        return qs

class OutboundBacklinkManager(models.Manager):
    def for_model(self, model):
        ct = ContentType.objects.get_for_model(model)
        qs = self.get_query_set().filter(content_type=ct)
        if isinstance(model, models.Model):
            qs = qs.filter(object_id=model._get_pk_val())
        return qs
