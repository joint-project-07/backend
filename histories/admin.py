from django.contrib import admin

from histories.models import History


@admin.register(History)
class HistoryAdmin(admin.ModelAdmin):
    pass
