from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    path('order/', include('apps.order.api.urls')),
    path('appointment/', include('apps.appointment.api.urls')),
    path('labs/', include('apps.lab.api.urls')),
    path('reports/', include('apps.report.api.urls')),
    path('accounts/', include('apps.account.api.urls')),
    path('form/', include('apps.form.api.urls')),
    path('doc/', SpectacularAPIView.as_view(), name='schema'),
    path('doc/swagger/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('doc/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]