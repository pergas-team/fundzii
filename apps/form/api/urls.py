from django.urls import path
from apps.form.api.views import FormListAPIView, FormDetailAPIView

urlpatterns = [

    path('forms/', FormListAPIView.as_view(), name='form-list'),
    path('forms/<int:pk>/', FormDetailAPIView.as_view(), name='form-detail'),

]
