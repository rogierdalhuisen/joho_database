import os
import requests
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import date
from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationError
from django.db import transaction

from .models import Klanten, Aanvragen, Landen

logger = logging.getLogger(__name__)


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


def parse_assuportal_record(record: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Vertaalt één record van de Assuportal API naar data voor Pydantic validatie.

    Args:
        record: Raw record van Assuportal API

    Returns:
        Tuple van (customer_data, application_data) dictionaries
    """
    # TODO: Pas de .get() veldnamen aan op basis van de JSON die je van Assuportal krijgt

    customer_data = {
        'emailadres': record.get('emailadres_klant'),
        'voorletters': record.get('voorletters'),
        'achternaam': record.get('familienaam'),
        'geboortedatum': record.get('geboortedatum'),
        'nationaliteit_land_code': record.get('landcode_nationaliteit')
    }

    application_data = {
        'bestemmings_land_code': record.get('polis', {}).get('bestemming_land'),
        'vertrekdatum': record.get('polis', {}).get('ingangsdatum')
    }

    # Verwijder keys waar de waarde None is
    clean_customer_data = {k: v for k, v in customer_data.items() if v is not None}
    clean_application_data = {k: v for k, v in application_data.items() if v is not None}

    return clean_customer_data, clean_application_data


def process_and_save_api_data(api_records: List[Dict[str, Any]]) -> Tuple[int, int]:
    """
    Loopt door alle records van de API, valideert met Pydantic en slaat ze op.

    Args:
        api_records: Lista van records van Assuportal API

    Returns:
        Tuple van (aantal_successen, aantal_fouten)
    """
    success_count = 0
    error_count = 0

    for record in api_records:
        record_id = record.get('uniek_id_van_assuportal', 'N/A')  # TODO: Pas dit ID aan

        try:
            # Parse en valideer met Pydantic
            customer_data_dict, application_data_dict = parse_assuportal_record(record)

            customer_data = CustomerData(**customer_data_dict)
            application_data = ApplicationData(**application_data_dict)

            # Opslaan in de database
            with transaction.atomic():
                customer, created = Klanten.objects.update_or_create(
                    emailadres=customer_data.emailadres,
                    defaults={
                        'voorletters': customer_data.voorletters,
                        'achternaam': customer_data.achternaam,
                        'geboortedatum': customer_data.geboortedatum,
                        'nationaliteit_land_code_id': customer_data.nationaliteit_land_code
                    }
                )

                Aanvragen.objects.create(
                    klant_id=customer,
                    bestemmings_land_code_id=application_data.bestemmings_land_code,
                    vertrekdatum=application_data.vertrekdatum
                )

                action = "aangemaakt" if created else "bijgewerkt"
                logger.info(f"Assuportal record {record_id}: Klant {action}, aanvraag aangemaakt")
                success_count += 1

        except ValidationError as e:
            logger.error(f"Validatiefout voor Assuportal record {record_id}: {e.errors()}")
            error_count += 1
        except Exception as e:
            logger.error(f"Databasefout voor Assuportal record {record_id}: {e}")
            error_count += 1

    return success_count, error_count


def fetch_data_from_assuportal() -> List[Dict[str, Any]]:
    """
    Voert de daadwerkelijke API-call uit naar Assuportal.

    Returns:
        List van records, of lege list bij fout
    """
    api_url = os.getenv('ASSUPORTAL_API_URL')
    api_key = os.getenv('ASSUPORTAL_API_KEY')

    if not api_url or not api_key:
        logger.critical("ASSUPORTAL_API_URL of ASSUPORTAL_API_KEY is niet geconfigureerd.")
        return []

    # TODO: Pas de authenticatiemethode aan op basis van het antwoord van Assuportal
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }

    # TODO: Voeg parameters toe voor filtering op basis van antwoord Assuportal
    params = {}

    try:
        logger.info(f"API-call naar Assuportal: {api_url}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()  # Stopt bij een error (4xx/5xx)

        # TODO: Pas de .get() key aan naar de juiste key waarin de resultaten staan
        return response.json().get('resultaten', [])  # Aanname
    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Assuportal mislukt: {e}")
        return []


# Hoofdfunctie om aan te roepen (bijvoorbeeld vanuit een Django management command)
def sync_assuportal_data():
    """
    Synchroniseert data van Assuportal API naar de database.
    """
    logger.info("Start Assuportal data synchronisatie")
    records = fetch_data_from_assuportal()

    if not records:
        logger.warning("Geen records opgehaald van Assuportal")
        return

    success, errors = process_and_save_api_data(records)
    logger.info(f"Assuportal sync voltooid: {success} succesvol, {errors} fouten")


# MISSING INFORMATION:
"""
Benodigde informatie voor Assuportal API integratie:

1. API Endpoints:
   - Wat is de base URL van de Assuportal API?
   - Welk endpoint levert klant- en aanvraaggegevens?

2. Authenticatie:
   - Welke authenticatiemethode (Bearer token, API key header, Basic auth)?
   - Waar krijg je de API credentials?

3. Data Structure:
   - Wat zijn de exacte veldnamen in de JSON response?
   - Welk datumformaat gebruiken ze?
   - Hoe zien landcodes eruit (NL, NLD, Netherlands)?

4. Environment variabelen (.env):
   ASSUPORTAL_API_URL=https://api.assuportal.com/v1/applications
   ASSUPORTAL_API_KEY=your_api_key_here

5. Rate Limiting:
   - Zijn er rate limits?
   - Moeten we pagination gebruiken?
"""
