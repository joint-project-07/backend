from django.contrib import admin

from recruitments.models import Recruitment


@admin.register(Recruitment)
class RecruitmentAdmin(admin.ModelAdmin):
    pass
