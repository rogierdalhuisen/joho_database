import os
import json
import logging
import hashlib
import hmac
from typing import Dict, Any, Optional, Tuple
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from .models import Klanten, Aanvragen, Landen

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
        logger.error("CRITICAL: WEBHOOK_SECRET_GRIP is not configured. Rejecting request.")
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


class CustomerData(BaseModel):
    """Pydantic model voor klantgegevens validatie."""
    emailadres: EmailStr
    voorletters: Optional[str] = Field(None, max_length=10)
    achternaam: str = Field(..., max_length=255)
    geboortedatum: Optional[date] = None
    nationaliteit_land_code: Optional[str] = Field(None, max_length=3)

    @field_validator('nationaliteit_land_code')
    @classmethod
    def validate_country_code(cls, v: Optional[str]) -> str:
        """Valideer of de landcode bestaat in de database."""
        if v and not Landen.objects.filter(land_code=v).exists():
            logger.warning(f"Onbekende landcode: {v}, standaard naar NLD")
            return 'NLD'
        return v or 'NLD'


class ApplicationData(BaseModel):
    """Pydantic model voor aanvraaggegevens validatie."""
    bestemmings_land_code: Optional[str] = Field(None, max_length=3)
    vertrekdatum: Optional[date] = None

    @field_validator('bestemmings_land_code')
    @classmethod
    def validate_destination_country(cls, v: Optional[str]) -> Optional[str]:
        """Valideer of de bestemmingslandcode bestaat in de database."""
        if v and not Landen.objects.filter(land_code=v).exists():
            raise ValueError(f"Onbekende bestemmingslandcode: {v}")
        return v


def parse_customer_data(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and map customer data from webhook form data.

    Args:
        form_data: Raw form data from GRIP webhook

    Returns:
        Dictionary with mapped field names for CustomerData
    """
    # TODO: Map actual field names once webhook structure is known
    mapped_data = {
        'emailadres': form_data.get('email') or form_data.get('emailAddress'),
        'voorletters': form_data.get('initials') or (form_data.get('firstName', '')[:10] if form_data.get('firstName') else None),
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
        form_data: Raw form data from GRIP webhook

    Returns:
        Dictionary with mapped field names for ApplicationData
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

    Validates ALL data first with Pydantic, then performs database operations only if everything is valid.

    Args:
        form_data: Raw form data from webhook

    Returns:
        Tuple of (customer_instance, application_instance, errors)
    """
    errors = []

    try:
        # Step 1: Parse and validate customer data with Pydantic - NO database operations yet
        customer_data_dict = parse_customer_data(form_data)
        customer_data = CustomerData(**customer_data_dict)

        # Step 2: Parse and validate application data with Pydantic - NO database operations yet
        application_data_dict = parse_application_data(form_data)
        application_data = ApplicationData(**application_data_dict)

        # Step 3: Only NOW start database transaction - all validation passed
        with transaction.atomic():
            # Create/update customer
            customer, created = Klanten.objects.update_or_create(
                emailadres=customer_data.emailadres,
                defaults={
                    'voorletters': customer_data.voorletters,
                    'achternaam': customer_data.achternaam,
                    'geboortedatum': customer_data.geboortedatum,
                    'nationaliteit_land_code_id': customer_data.nationaliteit_land_code
                }
            )

            # Create application
            application = Aanvragen.objects.create(
                klant_id=customer,
                bestemmings_land_code_id=application_data.bestemmings_land_code,
                vertrekdatum=application_data.vertrekdatum
            )

            logger.info(f"Successfully processed GRIP webhook: customer={customer.klant_id}, application={application.aanvraag_id}")

            return customer, application, errors

    except ValidationError as e:
        # Pydantic validation errors
        for error in e.errors():
            field = ' -> '.join(str(x) for x in error['loc'])
            message = error['msg']
            errors.append(f"Validation error: {field}: {message}")
        logger.error(f"GRIP webhook validation errors: {errors}")
        return None, None, errors
    except Exception as e:
        logger.error(f"Unexpected error processing GRIP webhook: {e}")
        errors.append(f"Processing error: {str(e)}")
        return None, None, errors


@csrf_exempt
@require_http_methods(["POST"])
def form_webhook(request):
    """
    Django view to receive form data webhooks from GRIP.

    Expected to be called at: /api/grip-webhook/
    """
    try:
        # Verify webhook signature for security
        webhook_secret = os.getenv('WEBHOOK_SECRET_GRIP')
        signature = request.headers.get('X-Signature') or request.headers.get('X-Hub-Signature-256')

        if webhook_secret and signature:
            if not verify_webhook_signature(request.body, signature, webhook_secret):
                logger.warning("Invalid GRIP webhook signature")
                return JsonResponse({'error': 'Invalid signature'}, status=401)

        # Parse JSON data
        try:
            form_data = json.loads(request.body)
        except json.JSONDecodeError:
            logger.error("Invalid JSON in GRIP webhook")
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        # Process form data
        customer, application, errors = process_webhook_data(form_data)

        if errors:
            logger.warning(f"GRIP webhook processing errors: {errors}")
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
        logger.error(f"GRIP webhook error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# Additional information still needed:
"""
MISSING INFORMATION NEEDED FOR GRIP WEBHOOK:

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
   WEBHOOK_SECRET_GRIP=your_shared_secret_here

4. URL Configuration:
   - Add to your Django urls.py:
     from comparator_app.webhook_grip import form_webhook
     path('api/grip-webhook/', form_webhook, name='grip_webhook')

5. Database:
   - Populate Landen table with valid codes
   - Run migrations: python manage.py makemigrations && python manage.py migrate

6. Testing:
   - Test webhook endpoint with curl or Postman
   - Confirm data mapping works correctly
"""
