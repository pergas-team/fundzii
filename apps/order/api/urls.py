from django.urls import path

from apps.order.api.views import OrderIssueView, OrderListView, OrderDetailView, OrderCompleteView, \
    OrderPaymentView, OrderCancelView, \
    PromotionCodeListView, PromotionCodeDetailView, PaymentRecordListView, \
    OrderBoughtListView, PaymentRecordManagerListView, \
    PaymentRecordConfirmDetailView, PaymentRecordTRefDetailView, ExcelProcessView, OrderPrePaymentView

# TicketManagerListView,TransactionDetailView,PromotionCodeStrView,TransactionListView,TransactionManagerListView
    # TicketListView, TicketDetailView
# SubscriptionManagerListView, SubscriptionListView, SubscriptionDetailView, PaymentRequestView, PaymentConfirmView, gateway, confirm,

urlpatterns = [

    # url(r'^balance/$', RequestBalanceView.as_view()),
    # url(r'^balance/list/$', BalanceListView.as_view()),
    # url(r'^balance/(?P<pk>[0-9]+)/$', BalanceItemView.as_view()),
    # url(r'^balance/(?P<pk>[0-9]+)/update/$', BalanceUpdateView.as_view()),
    # url(r'^balance/(?P<pk>[0-9]+)/result/$', BalanceResultView.as_view()),

    # url(r'^service/$', ServiceView.as_view()),
    # url(r'^service/list/$', ServiceListView.as_view()),
    # url(r'^service/vitrin/list/$', ServiceVitrinListView.as_view()),
    # url(r'^service/mine/list/$', OwnerServiceListView.as_view()),
    # url(r'^service/(?P<pk>[0-9]+)/update/$', ServiceItemView.as_view()),
    # url(r'^service/(?P<pk>[0-9]+)/$', ServiceRetrieveView.as_view()),
    # url(r'^service/code/(?P<service_code>.+)/$', ServiceCodeRetrieveView.as_view()),

    path('order/', OrderIssueView.as_view()),
    # path('order/check/', CheckOrderView.as_view()),
    path('order/list/', OrderListView.as_view()),
    path('order/bought/list/', OrderBoughtListView.as_view()),
    # path('order/owned/list/', OwnedOrderListView.as_view()),
    # url(r'^order/mine/list/$', OwnedOrderListView.as_view()),
    path('order/<int:pk>/', OrderDetailView.as_view()),
    path('order/<int:pk>/update/', OrderCompleteView.as_view()),
    # url(r'^order/(?P<pk>[0-9]+)/update/$', OrderUpdateView.as_view()),
    path('order/<int:pk>/pay/', OrderPaymentView.as_view()),
    path('order/<int:pk>/prepay/', OrderPrePaymentView.as_view()),
    path('order/<int:pk>/cancel/', OrderCancelView.as_view()),

    # url(r'^ticket/(?P<pk>[0-9]+)/delete/$', DeleteTicketView.as_view()),
    # url(r'^extension/(?P<pk>[0-9]+)/delete/$', DeleteExtensionView.as_view()),

    # path('ticket/manager/list/', TicketManagerListView.as_view()),
    # path('ticket/list/', TicketListView.as_view()),
    # path('ticket/<int:pk>/', TicketDetailView.as_view()),

    # path('subscription/manager/list/', SubscriptionManagerListView.as_view()),
    # path('subscription/list/', SubscriptionListView.as_view()),
    # path('subscription/<int:pk>/', SubscriptionDetailView.as_view()),


    # path('transaction/list/', TransactionListView.as_view()),
    # path('transaction/manager/list/', TransactionManagerListView.as_view()),
    # path('transaction/<int:pk>/', TransactionDetailView.as_view()),

   # path('charge/request/', PaymentRequestView.as_view()),
   # path('charge/confirm/', PaymentConfirmView.as_view()),

   # path('payment/process/', gateway),
   # path('payment/confirm/', confirm),

   path('payment/<str:id2>/confirm/', PaymentRecordConfirmDetailView.as_view()),

   path('promo-code/list/', PromotionCodeListView.as_view()),
   path('promo-code/<int:pk>/', PromotionCodeDetailView.as_view()),
   # path('promo-code/<str:code>/', PromotionCodeStrView.as_view()),

    path('payment-record/list/', PaymentRecordListView.as_view()),
    path('payment-record/<int:pk>/manager/', PaymentRecordTRefDetailView.as_view()),
    path('payment-record/manager/list/', PaymentRecordManagerListView.as_view()),
    path('payment-record/excel/', ExcelProcessView.as_view(), name='excel_process'),

    #    path('promo-codes/add/', AddPromotionCodeView.as_view()),
#    path('promo-codes/list/', PromotionCodeListView.as_view()),
#    path('promo-codes/promo-code/(?P<pk>[0-9]+)/update/', EditPromotionCodeView.as_view()),
#    path('promo-codes/promo-code/(?P<pk>[0-9]+)/', PromotionCodeItemView.as_view()),
]
