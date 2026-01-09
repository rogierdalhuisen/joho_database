import requests
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, date
import pytz
from django.db import transaction
from django.conf import settings

from .models import Relaties, Personen, Contracten, AdviesAanvragen

logger = logging.getLogger(__name__)

# Load environment variables via Django settings
def get_env(key, default=None):
    """Get environment variable through Django settings."""
    from decouple import config
    return config(key, default=default)


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def convert_invalid_date(date_string: Optional[str]) -> Optional[date]:
    """
    Converteer datum string naar date object, of None bij ongeldige datum.

    Args:
        date_string: Datum string uit API (bijv. "2020-01-15" of "0000-00-00")

    Returns:
        date object of None
    """
    if not date_string or date_string in ['0000-00-00', '']:
        return None

    try:
        return datetime.strptime(date_string, '%Y-%m-%d').date()
    except (ValueError, TypeError):
        logger.warning(f"Kon datum niet parsen: {date_string}")
        return None


def convert_invalid_datetime(datetime_string: Optional[str]) -> Optional[datetime]:
    """
    Converteer datetime string naar datetime object, of None bij ongeldige datetime.

    Args:
        datetime_string: Datetime string uit API (bijv. "2020-01-15 14:30:00" of "0000-00-00 00:00:00")

    Returns:
        datetime object of None (timezone-aware)
    """
    if not datetime_string or datetime_string in ['0000-00-00 00:00:00', '', '0000-00-00']:
        return None

    try:
        from django.utils import timezone
        # Parse as naive datetime
        naive_dt = datetime.strptime(datetime_string, '%Y-%m-%d %H:%M:%S')
        # Make timezone-aware (assume UTC from API)
        return timezone.make_aware(naive_dt, pytz.UTC)
    except (ValueError, TypeError):
        logger.warning(f"Kon datetime niet parsen: {datetime_string}")
        return None


# ============================================================================
# API FETCH FUNCTIONS
# ============================================================================

def fetch_relaties_list(page: int = 1, size: int = 50) -> Dict[str, Any]:
    """
    Haal een pagina met relaties op van de Assuportal API (LIST endpoint).

    Args:
        page: Paginanummer (start bij 1)
        size: Aantal records per pagina

    Returns:
        JSON response van de API of lege dict bij fout
    """
    api_url = get_env('ASSUPORTAL_RELATIES')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_RELATIES of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return {}

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'page': page,
        'size': size
    }

    try:
        logger.info(f"Fetching relaties: pagina {page}, size {size}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Relaties mislukt (pagina {page}): {e}")
        return {}


def fetch_relatie_detail(relatie_id: int) -> Dict[str, Any]:
    """
    Haal volledige details van één relatie op (DETAIL endpoint).

    Args:
        relatie_id: Het ID van de relatie

    Returns:
        JSON response van de API of lege dict bij fout
    """
    api_url = get_env('ASSUPORTAL_RELATIES')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_RELATIES of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return {}

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    detail_url = f"{api_url}/{relatie_id}"

    try:
        response = requests.get(detail_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Relatie detail {relatie_id} mislukt: {e}")
        return {}


def fetch_contracten_list(page: int = 1, size: int = 50) -> Dict[str, Any]:
    """
    Haal een pagina met contracten op van de Assuportal API (LIST endpoint).

    Args:
        page: Paginanummer (start bij 1)
        size: Aantal records per pagina

    Returns:
        JSON response van de API of lege dict bij fout
    """
    api_url = get_env('ASSUPORTAL_CONTRACTEN')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_CONTRACTEN of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return {}

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'page': page,
        'size': size
    }

    try:
        logger.info(f"Fetching contracten: pagina {page}, size {size}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Contracten mislukt (pagina {page}): {e}")
        return {}


def fetch_contract_detail(contract_id: int) -> Dict[str, Any]:
    """
    Haal volledige details van één contract op (DETAIL endpoint).

    Args:
        contract_id: Het ID van het contract

    Returns:
        JSON response van de API of lege dict bij fout
    """
    api_url = get_env('ASSUPORTAL_CONTRACTEN')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_CONTRACTEN of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return {}

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    detail_url = f"{api_url}/{contract_id}"

    try:
        response = requests.get(detail_url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Contract detail {contract_id} mislukt: {e}")
        return {}


# ============================================================================
# DATA EXTRACTION FUNCTIONS
# ============================================================================

def extract_email_list(api_data: Dict[str, Any]) -> List[str]:
    """
    Extraheer alle email adressen uit de detail API response.

    Args:
        api_data: De 'data' dict van de detail API response

    Returns:
        List van email adressen (strings)
    """
    emails = []

    # Email uit email_adressen array
    email_adressen = api_data.get('email_adressen', [])
    for email_obj in email_adressen:
        if email_obj.get('email'):
            emails.append(email_obj['email'])

    # Fallback: standaard_email uit LIST response
    if not emails and api_data.get('standaard_email'):
        emails.append(api_data['standaard_email'])

    return emails


# ============================================================================
# SAVE FUNCTIONS
# ============================================================================

def save_relatie_from_api(api_data: Dict[str, Any], use_detail: bool = False) -> Optional[Relaties]:
    """
    Sla een Relatie op vanuit API data (LIST of DETAIL).

    MERGE STRATEGIE: Als een relatie met dit email al bestaat vanuit een AdviesAanvraag
    (relatie_id=None, source='adviesaanvraag'), dan wordt deze relatie ge-upgrade met
    de API data in plaats van een nieuwe aan te maken.

    Args:
        api_data: De 'data' dict van de API response
        use_detail: True als api_data van DETAIL endpoint komt (heeft personen, adressen, etc)

    Returns:
        Relaties object of None bij fout
    """
    try:
        with transaction.atomic():
            # Basis velden (beschikbaar in LIST en DETAIL)
            relatie_id = api_data.get('id')
            hoofdnaam = api_data.get('naam')
            ts_aangemaakt = convert_invalid_datetime(api_data.get('ts_aangemaakt'))

            # Email adressen
            if use_detail:
                email_adressen = extract_email_list(api_data)
            else:
                # LIST response heeft alleen standaard_email
                standaard_email = api_data.get('standaard_email')
                email_adressen = [standaard_email] if standaard_email else []

            # MERGE LOGICA: Check of er al een "orphaned" relatie bestaat
            # Stap 1: Probeer te vinden op relatie_id
            try:
                relatie = Relaties.objects.get(relatie_id=relatie_id)
                # Bestaande API relatie gevonden, update deze
                relatie.hoofdnaam = hoofdnaam
                relatie.ts_aangemaakt = ts_aangemaakt
                relatie.email_adressen = email_adressen
                relatie.source = 'api'
                relatie.save()
                action = "bijgewerkt (bestaande API relatie)"
                logger.info(f"Relatie {relatie_id} ({hoofdnaam}): {action}")

            except Relaties.DoesNotExist:
                # Stap 2: Geen API relatie gevonden, check voor orphaned relatie met dit email
                orphaned_relatie = None
                if email_adressen:
                    for email in email_adressen:
                        # Zoek relatie die:
                        # 1. Nog geen relatie_id heeft (None)
                        # 2. Van formulier komt (source='adviesaanvraag')
                        # 3. Dit email bevat
                        orphaned_relatie = Relaties.objects.filter(
                            relatie_id__isnull=True,
                            source='adviesaanvraag',
                            email_adressen__contains=[email]
                        ).first()

                        if orphaned_relatie:
                            logger.info(f"MERGE: Orphaned relatie {orphaned_relatie.pk} matched met API relatie {relatie_id} via email {email}")
                            break

                if orphaned_relatie:
                    # MERGE: Update de orphaned relatie met API data
                    orphaned_relatie.relatie_id = relatie_id
                    orphaned_relatie.hoofdnaam = hoofdnaam
                    orphaned_relatie.ts_aangemaakt = ts_aangemaakt
                    orphaned_relatie.email_adressen = email_adressen
                    orphaned_relatie.source = 'api'
                    orphaned_relatie.save()
                    relatie = orphaned_relatie
                    action = "ge-merged (formulier → API)"
                    logger.info(f"Relatie {relatie_id} ({hoofdnaam}): {action}")
                else:
                    # Geen orphaned relatie gevonden, maak nieuwe aan
                    relatie = Relaties.objects.create(
                        relatie_id=relatie_id,
                        hoofdnaam=hoofdnaam,
                        ts_aangemaakt=ts_aangemaakt,
                        email_adressen=email_adressen,
                        source='api'
                    )
                    action = "aangemaakt (nieuwe API relatie)"
                    logger.info(f"Relatie {relatie_id} ({hoofdnaam}): {action}")

            # Als DETAIL: sla ook Personen op
            if use_detail:
                personen_data = api_data.get('personen', [])
                email_adressen_data = api_data.get('email_adressen', [])

                # Build lookup: persoon_id -> email
                email_lookup = {}
                for email_obj in email_adressen_data:
                    persoon_id = email_obj.get('persoon_id')
                    email = email_obj.get('email')
                    if persoon_id and email:
                        # Store first email per person (in case of multiple)
                        if persoon_id not in email_lookup:
                            email_lookup[persoon_id] = email

                # Verwijder oude personen (voor re-sync)
                relatie.personen.all().delete()

                # Voeg nieuwe personen toe met correct email
                for persoon in personen_data:
                    api_persoon_id = persoon.get('id')
                    persoon_email = email_lookup.get(api_persoon_id)  # Look up by person ID

                    Personen.objects.create(
                        relatie=relatie,
                        api_persoon_id=api_persoon_id,
                        persoon_naam=persoon.get('naam', ''),
                        persoon_email=persoon_email
                    )

                logger.debug(f"  → {len(personen_data)} personen opgeslagen")

            return relatie

    except Exception as e:
        logger.error(f"Fout bij opslaan Relatie {api_data.get('id')}: {e}")
        return None


def save_contract_from_api(api_data: Dict[str, Any]) -> Optional[Contracten]:
    """
    Sla een Contract op vanuit API data.

    Args:
        api_data: De 'data' dict van de API response (LIST of DETAIL)

    Returns:
        Contracten object of None bij fout
    """
    try:
        contract_id = api_data.get('id')
        relatie_id = api_data.get('relatie_id')

        # Check of Relatie bestaat
        try:
            relatie = Relaties.objects.get(relatie_id=relatie_id)
        except Relaties.DoesNotExist:
            logger.warning(f"Contract {contract_id}: Relatie {relatie_id} niet gevonden, skip")
            return None

        with transaction.atomic():
            # Datum conversies
            datum_ingang = convert_invalid_date(api_data.get('datum_ingang'))
            ts_aangemaakt = convert_invalid_datetime(api_data.get('ts_aangemaakt'))
            ts_gewijzigd = convert_invalid_datetime(api_data.get('ts_gewijzigd'))

            # Update or create Contract
            contract, created = Contracten.objects.update_or_create(
                contract_id=contract_id,
                defaults={
                    'polisnummer': api_data.get('polisnummer', ''),
                    'branche': api_data.get('branche'),
                    'relatie': relatie,
                    'datum_ingang': datum_ingang,
                    'ts_aangemaakt': ts_aangemaakt,
                    'ts_gewijzigd': ts_gewijzigd
                }
            )

            action = "aangemaakt" if created else "bijgewerkt"
            logger.info(f"Contract {contract_id} ({api_data.get('polisnummer')}): {action}")

            return contract

    except Exception as e:
        logger.error(f"Fout bij opslaan Contract {api_data.get('id')}: {e}")
        return None


# ============================================================================
# MATCHING FUNCTION FOR ADVIESAANVRAGEN
# ============================================================================

def find_or_create_relatie_by_email(email: str) -> Relaties:
    """
    Zoek een Relatie op basis van email, of maak een nieuwe aan.

    Deze functie wordt gebruikt wanneer een AdviesAanvraag binnenkomt met een email.
    Het zoekt in:
    1. Relaties.email_adressen JSONField
    2. Personen.persoon_email

    Als geen match: maak nieuwe Relatie aan met alleen email.

    Args:
        email: Email adres van de AdviesAanvraag

    Returns:
        Relaties object (bestaand of nieuw)
    """
    # Zoek in Relaties.email_adressen JSONField
    # Django JSONField contains lookup
    relatie = Relaties.objects.filter(email_adressen__contains=[email]).first()

    if relatie:
        logger.info(f"Email {email} gevonden in bestaande Relatie {relatie.relatie_id}")
        return relatie

    # Zoek in Personen.persoon_email
    persoon = Personen.objects.filter(persoon_email=email).first()
    if persoon:
        logger.info(f"Email {email} gevonden in Persoon {persoon.persoon_id}, linked to Relatie {persoon.relatie.relatie_id}")
        return persoon.relatie

    # Geen match: maak nieuwe Relatie
    logger.info(f"Email {email} niet gevonden, nieuwe Relatie aanmaken")
    relatie = Relaties.objects.create(
        relatie_id=None,  # Nog geen API ID
        hoofdnaam=None,
        email_adressen=[email],
        source='adviesaanvraag'
    )

    return relatie


# ============================================================================
# MAIN SYNC FUNCTIONS
# ============================================================================

def sync_relaties(page_size: int = 50, use_detail: bool = False, max_pages: Optional[int] = None) -> Tuple[int, int]:
    """
    Synchroniseer Relaties van Assuportal API naar database.

    Args:
        page_size: Aantal records per pagina
        use_detail: True om DETAIL endpoint te gebruiken (langzaam maar volledig)
        max_pages: Maximaal aantal paginas (voor testen), None = alle

    Returns:
        Tuple van (success_count, error_count)
    """
    logger.info("=== Start Relaties synchronisatie ===")

    success_count = 0
    error_count = 0
    page = 1

    while True:
        # Stop als max_pages bereikt
        if max_pages and page > max_pages:
            logger.info(f"Max pages ({max_pages}) bereikt, stoppen")
            break

        # Haal lijst op
        response = fetch_relaties_list(page=page, size=page_size)

        if not response or response.get('result') != 'ok':
            logger.error(f"Geen geldige response voor pagina {page}")
            break

        data_list = response.get('data', [])
        meta = response.get('meta', {})

        if not data_list:
            logger.info(f"Geen data op pagina {page}, stoppen")
            break

        logger.info(f"Pagina {page}/{meta.get('last_page', '?')}: {len(data_list)} relaties")

        # Verwerk elke relatie
        for relatie_data in data_list:
            relatie_id = relatie_data.get('id')

            # Als use_detail: haal volledige data op
            if use_detail:
                detail_response = fetch_relatie_detail(relatie_id)
                if detail_response and detail_response.get('result') == 'ok':
                    detail_data = detail_response.get('data', {})
                    result = save_relatie_from_api(detail_data, use_detail=True)
                else:
                    logger.error(f"Kon detail niet ophalen voor Relatie {relatie_id}")
                    result = None
            else:
                # Gebruik LIST data
                result = save_relatie_from_api(relatie_data, use_detail=False)

            if result:
                success_count += 1
            else:
                error_count += 1

        # Check of er een volgende pagina is
        current_page = meta.get('current_page')
        last_page = meta.get('last_page')

        if current_page and last_page and current_page >= last_page:
            logger.info("Laatste pagina bereikt")
            break

        page += 1

    logger.info(f"=== Relaties sync voltooid: {success_count} succesvol, {error_count} fouten ===")
    return success_count, error_count


def sync_contracten(page_size: int = 50, max_pages: Optional[int] = None) -> Tuple[int, int, int]:
    """
    Synchroniseer Contracten van Assuportal API naar database.

    Args:
        page_size: Aantal records per pagina
        max_pages: Maximaal aantal paginas (voor testen), None = alle

    Returns:
        Tuple van (success_count, error_count, skipped_count)
    """
    logger.info("=== Start Contracten synchronisatie ===")

    success_count = 0
    error_count = 0
    skipped_count = 0
    page = 1

    while True:
        # Stop als max_pages bereikt
        if max_pages and page > max_pages:
            logger.info(f"Max pages ({max_pages}) bereikt, stoppen")
            break

        # Haal lijst op
        response = fetch_contracten_list(page=page, size=page_size)

        if not response or response.get('result') != 'ok':
            logger.error(f"Geen geldige response voor pagina {page}")
            break

        data_list = response.get('data', [])
        meta = response.get('meta', {})

        if not data_list:
            logger.info(f"Geen data op pagina {page}, stoppen")
            break

        logger.info(f"Pagina {page}/{meta.get('last_page', '?')}: {len(data_list)} contracten")

        # Verwerk elk contract
        for contract_data in data_list:
            result = save_contract_from_api(contract_data)

            if result:
                success_count += 1
            elif result is None and contract_data.get('relatie_id'):
                # None betekent Relatie niet gevonden (zie save_contract_from_api)
                skipped_count += 1
            else:
                error_count += 1

        # Check of er een volgende pagina is
        current_page = meta.get('current_page')
        last_page = meta.get('last_page')

        if current_page and last_page and current_page >= last_page:
            logger.info("Laatste pagina bereikt")
            break

        page += 1

    logger.info(f"=== Contracten sync voltooid: {success_count} succesvol, {error_count} fouten, {skipped_count} geskipt ===")
    return success_count, error_count, skipped_count
