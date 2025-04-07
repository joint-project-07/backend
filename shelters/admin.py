from django.contrib import admin

from shelters.models import Shelter


@admin.register(Shelter)
class ShelterAdmin(admin.ModelAdmin):
    pass
