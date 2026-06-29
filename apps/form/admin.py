from django.contrib import admin

from apps.form.models import Form


@admin.register(Form)
class FormAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'updated_at')