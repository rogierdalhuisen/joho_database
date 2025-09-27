from django.urls import path
from . import api_grip

urlpatterns = [
    path('api/form-webhook/', api_grip.form_webhook, name='form_webhook'),
]