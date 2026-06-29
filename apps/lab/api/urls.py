from django.urls import path

from apps.lab.api.views import *
# from apps.lab.api.views import LaboratoryListAPIView, LaboratoryDetailAPIView, \
#     ExperimentListAPIView, ExperimentDetailAPIView, DeviceListAPIView, DeviceDetailAPIView, ParameterListAPIView, \
#     ParameterDetailAPIView, RequestDetailAPIView, RequestListAPIView, DepartmentListAPIView, DepartmentDetailAPIView, \
#     FormResponseListAPIView, FormResponseDetailAPIView, OwnedRequestListAPIView, OwnedRequestDetailAPIView, \
#     LabTypeListAPIView, LabTypeDetailAPIView, RequestChangeStatusAPIView, WorkflowDetailAPIView

urlpatterns = [

    path('form-responses/', FormResponseListAPIView.as_view(), name='form-responses-list'),
    path('form-responses/<int:pk>/', FormResponseDetailAPIView.as_view(), name='form-response-detail'),

    path('devices/', DeviceListAPIView.as_view(), name='devices-list'),
    path('devices/<int:pk>/', DeviceDetailAPIView.as_view(), name='device-detail'),

    path('parameters/', ParameterListAPIView.as_view(), name='parameters-list'),
    path('parameters/<int:pk>/', ParameterDetailAPIView.as_view(), name='parameter-detail'),

    path('parameters/pub/', ParameterPubListAPIView.as_view(), name='parameters-pub-list'),
    path('parameters/<int:pk>/pub/', ParameterPubDetailAPIView.as_view(), name='parameter-pub-detail'),

    path('requests/owned/', OwnedRequestListAPIView.as_view(), name='owned-requests-list'),
    path('requests/owned/<int:pk>/', OwnedRequestDetailAPIView.as_view(), name='owned-request-detail'),

    path('requests/<int:pk>/status/', RequestChangeStatusAPIView.as_view(), name='request-change-status'),
    path('requests/<int:pk>/result/', RequestResultAPIView.as_view(), name='request-result'),
    path('requests/<int:pk>/labsnet/', UpdateRequestLabsnetView.as_view(), name='request-labsnet'),

    path('requests/<int:pk>/recalculate/', UpdateRequestRecalculateView.as_view(), name='request-recalculate'),
    path('requests/<int:pk>/resend-labsnet/', UpdateRequestResendLabsnetView.as_view(), name='request-resend-labsnet'),

    path('requests/', RequestListAPIView.as_view(), name='requests-list'),
    path('requests/<int:pk>/', RequestDetailAPIView.as_view(), name='request-detail'),
    path('requests/<int:pk>/certificate', RequestCertificateAPIView.as_view(), name='request-detail'),
    path('requests/<int:pk>/request-certificate/', URequestCertificateAPIView.as_view(), name='certificate-request-detail'),

    path('department/', DepartmentListAPIView.as_view(), name='department-list'),
    path('department/<int:pk>/', DepartmentDetailAPIView.as_view(), name='department-detail'),

    path('lab-type/', LabTypeListAPIView.as_view(), name='lab-type-list'),
    path('lab-type/<int:pk>/', LabTypeDetailAPIView.as_view(), name='lab-type-detail'),

    path('workflow/', WorkflowListAPIView.as_view(), name='workflow-list'),
    path('workflow/<int:pk>/', WorkflowDetailAPIView.as_view(), name='workflow-detail'),

    path('results/', RequestResultAPIView.as_view(), name='results-list'),
    path('results/<int:pk>/', RequestResultDetailAPIView.as_view(), name='results-detail'),
]
