from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.fundzi.models import RequestHistory
from apps.fundzi.notifications import notify_status_change


@receiver(post_save, sender=RequestHistory, dispatch_uid='fundzi_request_history_notify')
def on_request_history_created(sender, instance, created, **kwargs):
    """Every status transition (initial submit, admin change, Django admin change)
    creates a RequestHistory row, so this is the single chokepoint for
    notifications."""
    if not created:
        return
    notify_status_change(instance.request, instance.from_status, instance.to_status)
