import jdatetime
from django.db.models import Sum
from django.db.models.signals import post_save
from django.dispatch import receiver
from rest_framework import status
from rest_framework.response import Response

from apps.account.models import Notification, OTPserver
from apps.lab.models import FormResponse, Request, Status

processing_request_signal = False
processing_formresponse_signal = False

@receiver(post_save, sender=Request)
def create_form_responses(sender, instance, created, **kwargs):
    global processing_request_signal

    if created or processing_request_signal:
        return

    processing_request_signal = True
    try:
        if not instance.sample_check and instance.is_completed:
            form_responses = FormResponse.objects.filter(request=instance, is_main=True)
            for form_response in form_responses:
                copies_needed = form_response.response_count - 1
                main_response = form_response
                if copies_needed > 0 and not form_response.copy_check:
                    for _ in range(copies_needed):
                        new_response = FormResponse.objects.create(request=main_response.request,
                                                                    form_number=main_response.form_number,
                                                                    response=main_response.response,
                                                                    response_json=main_response.response_json,
                                                                    is_main=False,
                                                                    parent=main_response)

            form_responses.update(copy_check=True)
            instance.sample_check = True
            instance.save()
            if instance.has_parent_request:
                instance.parent_request.set_price()
    finally:
        processing_request_signal = False


@receiver(post_save, sender=FormResponse)
def create_form_number(sender, instance, created, **kwargs):
    global processing_formresponse_signal

    if processing_formresponse_signal:
        return

    processing_formresponse_signal = True
    try:
        if created or not instance.form_number:
            instance.set_form_number()
        instance.request.set_price()
    finally:
        processing_formresponse_signal = False


@receiver(post_save, sender=Request)
def create_request_number(sender, instance, created, **kwargs):
    global processing_request_signal

    if processing_request_signal:
        return

    processing_request_signal = True
    try:
        if not instance.request_number and not instance.has_parent_request:
            date_code = jdatetime.datetime.now().strftime('%Y%m')
            month_code = instance.current_month_counter() + 1
            instance.request_number = f'{date_code[1:]}-{month_code:04d}'
            instance.save()
        if not instance.request_number and instance.has_parent_request:
            if not instance.parent_request.request_number:
                date_code = jdatetime.datetime.now().strftime('%Y%m')
                month_code = instance.parent_request.current_month_counter() + 1
                instance.parent_request.request_number = f'{date_code[1:]}-{month_code:04d}'
                instance.parent_request.save()
            child_requests = instance.parent_request.child_requests.all()
            instance.request_number = f'{instance.parent_request.request_number}-{child_requests.count():02d}'
            instance.save()
    except Exception as e:
        raise Exception
    finally:
        processing_request_signal = False

#
# @receiver(post_save, sender=Request)
# def create_form_responses(sender, instance, created, **kwargs):
#     if created:
#         return
#     if not instance.sample_check and instance.is_completed:
#         form_responses = FormResponse.objects.filter(request=instance, is_main=True)
#         for form_response in form_responses:
#             copies_needed = form_response.response_count - 1
#             if copies_needed > 0 and not form_response.copy_check:
#                 for _ in range(copies_needed):
#                     new_response = form_response
#                     new_response.pk = None
#                     new_response.is_main = False
#                     new_response.save()
#         form_responses.update(copy_check=True)
#         instance.sample_check = True
#         instance.save()
#
#
# @receiver(post_save, sender=FormResponse)
# def create_form_number(sender, instance, created, **kwargs):
#     if created or not instance.form_number:
#         instance.set_form_number()
#     instance.request.set_price()
#
#
# @receiver(post_save, sender=Request)
# def create_form_number(sender, instance, created, **kwargs):
#     if created or not instance.request_number:
#         date_code = jdatetime.datetime.now().strftime('%Y%m')
#         mounth_code = instance.current_month_counter() + 1
#         instance.request_number = f'{date_code[1:]}-{mounth_code:04d}'
#         instance.save()

@receiver(post_save, sender=Status)
def set_request_status_notification(sender, instance, created, **kwargs):
    if created and instance.request.is_completed and not instance.request.parent_request:
        content = f' وضعیت درخواست شماره {str(instance.request.request_number).split("-")[1]}-{str(instance.request.request_number).split("-")[0]} به {instance.step.name} تغییر کرد'
        Notification.objects.create(user=instance.request.owner, type='info', title='تغییر وضعیت درخواست', content=content)
        sms_server = OTPserver.objects.all().first()
        phone_number = str(instance.request.owner.username).replace("+98", "0")
        sms = sms_server.send_quick_message([phone_number], content)
        if 0 <= sms['statusCode'] <= 4:
            return Response({"detail": f"کد ارسال شد.", "message": sms['message']}, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "خطا در ارسال کد یکبارمصرف.", "message": sms['message']},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)