import os
import json
import logging
import hashlib
import hmac
from typing import Dict, Any, Optional, Tuple
from django import forms
from django.db import transaction
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from .models import Klanten, Aanvragen, Countries

logger = logging.getLogger(__name__)


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify webhook signature for security.

    Args:
        payload: Raw request body
        signature: Signature from webhook header
        secret: Webhook secret from environment

    Returns:
        True if signature is valid
    """
    if not secret:
        logger.error("CRITICAL: WEBHOOK_SECRET is not configured. Rejecting request.")
        return False  # Always fail if secret is missing - fail-closed security

    expected_signature = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()

    # Remove 'sha256=' prefix if present
    if signature.startswith('sha256='):
        signature = signature[7:]

    return hmac.compare_digest(expected_signature, signature)

class CustomerDataForm(forms.Form):
    """
    Form for validating customer data from webhook.
    """
    emailadres = forms.EmailField(required=True)
    voorletters = forms.CharField(max_length=10, required=False)
    achternaam = forms.CharField(max_length=255, required=True)
    geboortedatum = forms.DateField(required=False)
    nationaliteit_land_code = forms.CharField(max_length=3, required=False)

    def clean_nationaliteit_land_code(self):
        """Validate country code exists in database."""
        country_code = self.cleaned_data.get('nationaliteit_land_code')
        if country_code and not Countries.objects.filter(country_code=country_code).exists():
            logger.warning(f"Unknown country code: {country_code}, defaulting to NLD")
            return 'NLD'
        return country_code or 'NLD'


class ApplicationDataForm(forms.Form):
    """
    Form for validating application data from webhook.
    """
    bestemmings_land_code = forms.CharField(max_length=3, required=False)
    vertrekdatum = forms.DateField(required=False)

    def clean_bestemmings_land_code(self):
        """Validate destination country code exists in database."""
        country_code = self.cleaned_data.get('bestemmings_land_code')
        if country_code and not Countries.objects.filter(country_code=country_code).exists():
            raise forms.ValidationError(f"Unknown destination country code: {country_code}")
        return country_code


def parse_customer_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and map customer data from webhook form data.

    Args:
        form_data: Raw form data from external company

    Returns:
        Dictionary with mapped field names for CustomerDataForm
    """
    # TODO: Map actual field names once webhook structure is known
    mapped_data = {
        'emailadres': form_data.get('email') or form_data.get('emailAddress'),
        'voorletters': form_data.get('initials') or form_data.get('firstName', '')[:3],
        'achternaam': form_data.get('lastName') or form_data.get('surname'),
        'geboortedatum': form_data.get('dateOfBirth') or form_data.get('birthDate'),
        'nationaliteit_land_code': form_data.get('nationality')
    }

    # Remove None values
    return {k: v for k, v in mapped_data.items() if v is not None}


def parse_application_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and map application data from webhook form data.

    Args:
        form_data: Raw form data from external company

    Returns:
        Dictionary with mapped field names for ApplicationDataForm
    """
    # TODO: Map actual field names once webhook structure is known
    mapped_data = {
        'bestemmings_land_code': form_data.get('destination') or form_data.get('destinationCountry'),
        'vertrekdatum': form_data.get('departureDate') or form_data.get('startDate'),
    }

    # Remove None values
    return {k: v for k, v in mapped_data.items() if v is not None}


def process_webhook_data(form_data: Dict[str, Any]) -> Tuple[Optional[Klanten], Optional[Aanvragen], list]:
    """
    Process webhook form data and save to database atomically.

    Validates ALL data first, then performs database operations only if everything is valid.

    Args:
        form_data: Raw form data from webhook

    Returns:
        Tuple of (customer_instance, application_instance, errors)
    """
    errors = []

    try:
        # Step 1: Parse and validate customer data - NO database operations yet
        customer_data = parse_customer_data(form_data)
        customer_form = CustomerDataForm(customer_data)

        if not customer_form.is_valid():
            errors.extend([f"Customer validation: {field}: {error[0]}"
                         for field, error in customer_form.errors.items()])
            return None, None, errors

        # Step 2: Parse and validate application data - NO database operations yet
        application_data = parse_application_data(form_data)
        application_form = ApplicationDataForm(application_data)

        if not application_form.is_valid():
            errors.extend([f"Application validation: {field}: {error[0]}"
                         for field, error in application_form.errors.items()])
            return None, None, errors

        # Step 3: Only NOW start database transaction - all validation passed
        with transaction.atomic():
            # Create/update customer
            customer_clean_data = customer_form.cleaned_data
            email = customer_clean_data.pop('emailadres')

            customer, created = Klanten.objects.update_or_create(
                emailadres=email,
                defaults=customer_clean_data
            )

            # Create application
            application_clean_data = application_form.cleaned_data
            application_clean_data['klant_id'] = customer

            application = Aanvragen.objects.create(**application_clean_data)

            logger.info(f"Successfully processed webhook: customer={customer.klant_id}, application={application.aanvraag_id}")

            return customer, application, errors

    except Exception as e:
        logger.error(f"Unexpected error processing webhook: {e}")
        errors.append(f"Processing error: {e}")
        return None, None, errors


@csrf_exempt
@require_http_methods(["POST"])
def form_webhook(request):
    """
    Django view to receive form data webhooks from external company.

    Expected to be called at: /api/form-webhook/
    """
    try:
        # Verify webhook signature for security
        webhook_secret = os.getenv('WEBHOOK_SECRET')
        signature = request.headers.get('X-Signature') or request.headers.get('X-Hub-Signature-256')

        if webhook_secret and signature:
            if not verify_webhook_signature(request.body, signature, webhook_secret):
                logger.warning("Invalid webhook signature")
                return JsonResponse({'error': 'Invalid signature'}, status=401)

        # Parse JSON data
        try:
            form_data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in webhook")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Process form data
        customer, application, errors = process_webhook_data(form_data)

        if errors:
            logger.warning(f"Webhook processing errors: {errors}")
            return JsonResponse({
                'success': False,
                'errors': errors,
                'customer_id': customer.klant_id if customer else None,
                'application_id': application.aanvraag_id if application else None
            }, status=400)

        return JsonResponse({
            'success': True,
            'customer_id': customer.klant_id,
            'application_id': application.aanvraag_id,
            'message': 'Form data processed successfully'
        })

    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Additional information still needed:
"""
MISSING INFORMATION NEEDED FOR WEBHOOK:

1. Webhook Data Structure:
   - Exact field names they send (email vs emailAddress, etc.)
   - Date formats (ISO 8601, DD-MM-YYYY, etc.)
   - Country code format (ISO 2-letter like 'NL', 3-letter like 'NLD', etc.)
   - Example webhook payload JSON

2. Security:
   - How they sign webhooks (header name, algorithm)
   - Webhook secret/key for verification
   - IP whitelist if needed

3. Environment Setup (.env file):
   WEBHOOK_SECRET=your_shared_secret_here

4. URL Configuration:
   - Add to your Django urls.py:
     from comparator_app.api_grip import form_webhook
     path('api/form-webhook/', form_webhook, name='form_webhook')

5. Database:
   - Populate Countries table with valid codes
   - Run migrations: python manage.py makemigrations && python manage.py migrate

6. Testing:
   - Test webhook endpoint with curl or Postman
   - Confirm data mapping works correctly
"""