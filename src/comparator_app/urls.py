from django.urls import path
from . import webhook_grip

urlpatterns = [
    path('api/form-webhook/', webhook_grip.form_webhook, name='form_webhook'),
]