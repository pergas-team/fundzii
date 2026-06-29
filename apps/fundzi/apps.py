from django.apps import AppConfig


class FundziConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.fundzi'
    verbose_name = 'Fundzi'

    def ready(self):
        from apps.fundzi import signals  # noqa: F401
