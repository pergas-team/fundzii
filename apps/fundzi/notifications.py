"""Notification service layer for Fundzi.

A single entry point (``notify_status_change``) is called whenever a
``RequestHistory`` row is created. It always records an in-app notification and,
when enabled via settings, dispatches the same message over SMS / email through
pluggable, side-effect-isolated channel functions.

The channels are intentionally no-ops by default so the system works without any
external provider; wiring a real SMS/email backend only requires implementing the
``_send_sms`` / ``_send_email`` helpers (or pointing them at the phase-1 OTP SMS
provider) and turning the matching settings flag on.
"""

from django.conf import settings
from django.utils import timezone

from apps.fundzi.models import Notification, WorkflowStep


# Statuses worth notifying the applicant about over external channels (SMS/email).
# In-app notifications are always created for every change.
EXTERNAL_NOTIFY_STATUSES = {
    'needs_more_information',
    'offer_sent',
    'approved',
    'rejected',
}


def step_title(request, status_key):
    """Resolve a status key to its localized WorkflowStep title, falling back to
    the key itself if the step can't be found."""
    if not status_key:
        return ''
    workflow = getattr(request.service, 'workflow', None)
    if workflow:
        step = workflow.steps.filter(key=status_key).first()
        if step:
            return step.title
    return status_key.replace('_', ' ')


def build_message(request, from_status, to_status):
    """Return (kind, title, body) for a status transition."""
    to_title = step_title(request, to_status)
    if not from_status:
        return (
            'request_submitted',
            'درخواست شما ثبت شد',
            f'درخواست شما با کد رهگیری {request.tracking_code} ثبت شد و در وضعیت «{to_title}» قرار گرفت.',
        )
    return (
        'status_changed',
        'وضعیت درخواست شما تغییر کرد',
        f'وضعیت درخواست {request.tracking_code} به «{to_title}» تغییر کرد.',
    )


def notify_status_change(request, from_status, to_status):
    """Create an in-app notification for the request owner and dispatch external
    channels when enabled. Safe to call inside the RequestHistory post_save
    signal; failures in external channels never raise."""
    kind, title, body = build_message(request, from_status, to_status)

    notification = Notification.objects.create(
        user=request.user,
        request=request,
        kind=kind,
        channel='in_app',
        title=title,
        body=body,
        status='sent',
        sent_at=timezone.now(),
        metadata={'from_status': from_status, 'to_status': to_status},
    )

    if to_status in EXTERNAL_NOTIFY_STATUSES:
        phone = request.user.get_username()
        if getattr(settings, 'FUNDZI_SMS_NOTIFICATIONS_ENABLED', False):
            _dispatch(request, 'sms', title, body, phone, lambda: _send_sms(phone, body))
        if getattr(settings, 'FUNDZI_EMAIL_NOTIFICATIONS_ENABLED', False):
            email = getattr(request.user, 'email', '') or ''
            if email:
                _dispatch(request, 'email', title, body, email, lambda: _send_email(email, title, body))

    return notification


def _dispatch(request, channel, title, body, target, sender):
    """Run a channel sender, logging the outcome as a Notification row so external
    delivery attempts are auditable (NotificationLog behaviour)."""
    log = Notification.objects.create(
        user=request.user,
        request=request,
        kind='status_changed',
        channel=channel,
        title=title,
        body=body,
        status='pending',
        metadata={'target': target},
    )
    try:
        sender()
        log.status = 'sent'
        log.sent_at = timezone.now()
    except Exception as exc:  # external channels must never break the request flow
        log.status = 'failed'
        log.metadata = {**log.metadata, 'error': str(exc)}
    log.save(update_fields=['status', 'sent_at', 'metadata'])
    return log


def _send_sms(phone, body):
    """Placeholder SMS sender. Wire to the real provider in phase 1."""
    raise NotImplementedError('SMS provider not configured')


def _send_email(email, subject, body):
    """Placeholder email sender."""
    from django.core.mail import send_mail

    send_mail(subject, body, getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@fundzi.ir'), [email])
