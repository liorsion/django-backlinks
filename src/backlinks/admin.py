from django.contrib import admin
from backlinks.models import InboundBacklink, OutboundBacklink


class InboundBacklinkAdmin(admin.ModelAdmin):
    list_filter = ('status', )


class OutboundBacklinkAdmin(admin.ModelAdmin):
    list_filter = ('status', )

admin.site.register(InboundBacklink, InboundBacklinkAdmin)
admin.site.register(OutboundBacklink, OutboundBacklinkAdmin)
