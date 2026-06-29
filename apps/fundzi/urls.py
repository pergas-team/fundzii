from django.urls import path

from apps.fundzi import views


urlpatterns = [
    path('', views.service_list_page, name='fundzi-home'),
    path('services/<slug:slug>/', views.service_detail_page, name='fundzi-service-page'),
    path('services/<slug:slug>/request/', views.service_request_page, name='fundzi-request-create-page'),
    path('requests/', views.request_dashboard_page, name='fundzi-dashboard-page'),
    path('requests/<int:pk>/', views.request_detail_page, name='fundzi-request-page'),
]
