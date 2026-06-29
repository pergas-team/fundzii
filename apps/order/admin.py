from django.contrib import admin

from django.contrib import admin

# Register your models here.
from django.db.models import Count

from apps.order.models import PromotionCode, Order, PaymentRecord, Transaction, Ticket
from apps.order.sharifpayment import SharifPayment
from django.contrib import messages


class PromotionCodeAdmin(admin.ModelAdmin):
    list_display = ['code', 'percent_off', 'usable_count', 'used_count', 'active']


admin.site.register(PromotionCode, PromotionCodeAdmin)


@admin.action(description="Show Duplicate Orders")
def show_duplicate_orders(modeladmin, request, queryset):
    duplicate_orders = (
        Order.objects
        .values('request')  # گروه‌بندی بر اساس `request`
        .annotate(order_count=Count('id'))  # شمارش تعداد سفارش‌ها
        .filter(order_count__gt=1)  # فقط درخواست‌هایی که بیش از یک سفارش دارند
    )

    if not duplicate_orders.exists():
        modeladmin.message_user(request, "هیچ سفارش تکراری پیدا نشد.", messages.WARNING)
        return

    message = "📌 **سفارش‌های تکراری و تعداد پرداخت‌های آن‌ها:**\n"

    for duplicate in duplicate_orders:
        request_id = duplicate['request']
        orders = Order.objects.filter(request_id=request_id).order_by('-created_at')  # مرتب‌سازی جدیدترین به قدیمی‌ترین

        for order in orders:
            payment_count = PaymentRecord.objects.filter(order=order).count()
            message += f"\norder: **{order.id}** (Request ID: {request_id}) - PR: {payment_count}"

    modeladmin.message_user(request, message, messages.INFO)


@admin.action(description="Delete Duplicate Orders (Safe)")
def delete_duplicate_orders_safe(modeladmin, request, queryset):
    """
    حذف سفارش‌هایی که بیش از یک مورد برای یک `Request` وجود دارند،
    اما هیچ تراکنش (`Transaction`) یا بلیط (`Ticket`) ندارند.
    """
    duplicate_orders = (
        Order.objects
        .values('request')  # گروه‌بندی بر اساس `request`
        .annotate(order_count=Count('id'))  # شمارش تعداد سفارش‌ها
        .filter(order_count__gt=1)  # فقط درخواست‌هایی که بیش از یک سفارش دارند
    )

    orders_to_delete = Order.objects.none()  # مجموعه خالی برای ذخیره سفارش‌های قابل حذف

    for duplicate in duplicate_orders:
        request_id = duplicate['request']
        orders = Order.objects.filter(request_id=request_id).order_by('-created_at')  # جدیدترین‌ها بالاتر

        deletable_orders = []
        for order in orders[1:]:  # حداقل یک سفارش باقی بماند، بقیه بررسی شوند
            has_transactions = Transaction.objects.filter(order=order).exists()
            has_tickets = Ticket.objects.filter(order=order).exists()
            has_payments = PaymentRecord.objects.filter(order=order).exists()

            if not has_transactions and not has_tickets and not has_payments:
                deletable_orders.append(order.id)  # فقط سفارش‌های امن برای حذف

        orders_to_delete |= Order.objects.filter(id__in=deletable_orders)

    deleted_count = orders_to_delete.count()
    orders_to_delete.delete()

    if deleted_count > 0:
        modeladmin.message_user(request, f"{deleted_count} سفارش تکراری بدون پرداخت، تراکنش یا بلیط حذف شد.", messages.SUCCESS)
    else:
        modeladmin.message_user(request, "هیچ سفارش تکراری بدون پرداخت، تراکنش یا بلیط برای حذف پیدا نشد.", messages.WARNING)

@admin.action(description="Delete Duplicate Orders")
def delete_duplicate_orders(modeladmin, request, queryset):
    duplicate_orders = (
        Order.objects
        .values('request')
        .annotate(order_count=Count('id'))
        .filter(order_count__gt=1)
    )

    orders_to_delete = Order.objects.none()

    for duplicate in duplicate_orders:
        request_id = duplicate['request']
        orders = Order.objects.filter(request_id=request_id).order_by('-created_at')
        deletable_orders = [order for order in orders if not order.order_payment_records.exists()]

        if len(deletable_orders) > 1:
            orders_to_delete |= Order.objects.filter(id__in=[o.id for o in deletable_orders[1:]])

    deleted_count = orders_to_delete.count()
    for order_del in orders_to_delete:
        try:
            order_del.delete()
        except:
            pass
    # orders_to_delete.delete()

    if deleted_count > 0:
        modeladmin.message_user(request, f"{deleted_count} سفارش تکراری بدون پرداخت حذف شد.", messages.SUCCESS)
    else:
        modeladmin.message_user(request, "هیچ سفارشی برای حذف پیدا نشد.", messages.WARNING)

class OrderAdmin(admin.ModelAdmin):
    list_display = ['buyer', 'order_type', 'order_status', 'amount', 'paid', 'order_code', 'created_at', 'updated_at']
    actions = [delete_duplicate_orders_safe, delete_duplicate_orders, show_duplicate_orders]

admin.site.register(Order, OrderAdmin)

def check_pay(modeladmin, request, queryset):
    for payment_record in queryset:
        SharifPayment().pay_confirm(payment_record, 0)
        modeladmin.message_user(request, "Checked PaymentRecord.", messages.SUCCESS)

check_pay.short_description = "Check Pay"

class PaymentRecordAdmin(admin.ModelAdmin):
    # list_display = ['payer', 'order', 'payment_type', 'amount', 'successful', 'charged', 'transaction_code', 'created_at', 'updated_at']
    list_display = ['payer', 'order', 'payment_type', 'settlement_type', 'amount', 'successful', 'charged',
                    'transaction_code', 'tref', 'payment_order_id', 'called_back',
                    'is_returned', 'is_lock', 'log_text', 'created_at', 'updated_at']
    actions = [check_pay]

    # def check_pay():
    #
    #     pay_confirm(self, payment_record, Result):

admin.site.register(PaymentRecord, PaymentRecordAdmin)


class TransactionAdmin(admin.ModelAdmin):
    list_display = ['profile', 'order', 'amount', 'returned', 'created_at', 'updated_at']


admin.site.register(Transaction, TransactionAdmin)

