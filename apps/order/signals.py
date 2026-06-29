from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.order.models import PaymentRecord
from apps.lab.tasks import verify_payment_record


@receiver(post_save, sender=PaymentRecord)
def create_pr_set_auto_verify(sender, instance, created, **kwargs):
    # try:
    if created:
        verify_payment_record.apply_async(args=[instance.id], countdown=6 * 60)
    # except:
    #     pass
