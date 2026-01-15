import requests
import logging
from typing import Dict, Any, List, Tuple, Optional
from datetime import datetime, date
import pytz
from django.db import transaction
from django.conf import settings
from pydantic import ValidationError

from .models import Relaties, Personen, Contracten, AdviesAanvragen
from .schemas_assuportal import (
    AssuportalRelatiesAPIResponse,
    AssuportalRelatieDetailAPIResponse,
    AssuportalContractenAPIResponse,
    AssuportalContractDetailAPIResponse,
    AssuportalRelatieListItem,
    AssuportalRelatieDetail,
    AssuportalContract,
    RelatieInput,
    PersoonInput,
    ContractInput,
)

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

def fetch_relaties_list(
    page: int = 1,
    size: int = 50,
    datum_van: Optional[date] = None,
    datum_tot: Optional[date] = None
) -> Optional[AssuportalRelatiesAPIResponse]:
    """
    Haal een pagina met relaties op van de Assuportal API (LIST endpoint) met validatie.

    Args:
        page: Paginanummer (start bij 1)
        size: Aantal records per pagina
        datum_van: Filter voor relaties aangemaakt/gewijzigd vanaf deze datum (optioneel)
        datum_tot: Filter voor relaties aangemaakt/gewijzigd tot deze datum (optioneel)

    Returns:
        Validated AssuportalRelatiesAPIResponse of None bij fout
    """
    api_url = get_env('ASSUPORTAL_RELATIES')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_RELATIES of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return None

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'page': page,
        'size': size
    }

    # Add date filters if provided
    if datum_van:
        params['filter[datum_van]'] = datum_van.strftime('%Y-%m-%d')
    if datum_tot:
        params['filter[datum_tot]'] = datum_tot.strftime('%Y-%m-%d')

    try:
        filter_info = ""
        if datum_van or datum_tot:
            filter_info = f" (filter: {datum_van or 'begin'} tot {datum_tot or 'eind'})"
        logger.info(f"Fetching relaties: pagina {page}, size {size}{filter_info}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        # Validate with Pydantic
        try:
            validated_data = AssuportalRelatiesAPIResponse(**raw_data)
            logger.info(f"✓ Relaties API success: {len(validated_data.data)} items gevalideerd")
            return validated_data
        except ValidationError as e:
            logger.error(f"Relaties API response validation failed: {e}")
            logger.error(f"Raw response (first 500 chars): {str(raw_data)[:500]}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Relaties mislukt (pagina {page}): {e}")
        return None


def fetch_relatie_detail(relatie_id: int) -> Optional[AssuportalRelatieDetailAPIResponse]:
    """
    Haal volledige details van één relatie op (DETAIL endpoint) met validatie.

    Args:
        relatie_id: Het ID van de relatie

    Returns:
        Validated AssuportalRelatieDetailAPIResponse of None bij fout
    """
    api_url = get_env('ASSUPORTAL_RELATIES')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_RELATIES of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return None

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    detail_url = f"{api_url}/{relatie_id}"

    try:
        response = requests.get(detail_url, headers=headers, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        # Validate with Pydantic
        try:
            validated_data = AssuportalRelatieDetailAPIResponse(**raw_data)
            return validated_data
        except ValidationError as e:
            logger.error(f"Relatie detail API validation failed for {relatie_id}: {e}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Relatie detail {relatie_id} mislukt: {e}")
        return None


def fetch_contracten_list(
    page: int = 1,
    size: int = 50,
    datum_van: Optional[date] = None,
    datum_tot: Optional[date] = None
) -> Optional[AssuportalContractenAPIResponse]:
    """
    Haal een pagina met contracten op van de Assuportal API (LIST endpoint) met validatie.

    Args:
        page: Paginanummer (start bij 1)
        size: Aantal records per pagina
        datum_van: Filter voor contracten aangemaakt/gewijzigd vanaf deze datum (optioneel)
        datum_tot: Filter voor contracten aangemaakt/gewijzigd tot deze datum (optioneel)

    Returns:
        Validated AssuportalContractenAPIResponse of None bij fout
    """
    api_url = get_env('ASSUPORTAL_CONTRACTEN')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_CONTRACTEN of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return None

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    params = {
        'page': page,
        'size': size
    }

    # Add date filters if provided
    if datum_van:
        params['filter[datum_van]'] = datum_van.strftime('%Y-%m-%d')
    if datum_tot:
        params['filter[datum_tot]'] = datum_tot.strftime('%Y-%m-%d')

    try:
        filter_info = ""
        if datum_van or datum_tot:
            filter_info = f" (filter: {datum_van or 'begin'} tot {datum_tot or 'eind'})"
        logger.info(f"Fetching contracten: pagina {page}, size {size}{filter_info}")
        response = requests.get(api_url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        # Validate with Pydantic
        try:
            validated_data = AssuportalContractenAPIResponse(**raw_data)
            logger.info(f"✓ Contracten API success: {len(validated_data.data)} items gevalideerd")
            return validated_data
        except ValidationError as e:
            logger.error(f"Contracten API response validation failed: {e}")
            logger.error(f"Raw response (first 500 chars): {str(raw_data)[:500]}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Contracten mislukt (pagina {page}): {e}")
        return None


def fetch_contract_detail(contract_id: int) -> Optional[AssuportalContractDetailAPIResponse]:
    """
    Haal volledige details van één contract op (DETAIL endpoint) met validatie.

    Args:
        contract_id: Het ID van het contract

    Returns:
        Validated AssuportalContractDetailAPIResponse of None bij fout
    """
    api_url = get_env('ASSUPORTAL_CONTRACTEN')
    api_token = get_env('ASSUPORTAL_API_TOKEN')

    if not api_url or not api_token:
        logger.critical("ASSUPORTAL_CONTRACTEN of ASSUPORTAL_API_TOKEN niet geconfigureerd in .env")
        return None

    headers = {
        'Authorization': f'Bearer {api_token}',
        'Content-Type': 'application/json'
    }

    detail_url = f"{api_url}/{contract_id}"

    try:
        response = requests.get(detail_url, headers=headers, timeout=30)
        response.raise_for_status()
        raw_data = response.json()

        # Validate with Pydantic
        try:
            validated_data = AssuportalContractDetailAPIResponse(**raw_data)
            return validated_data
        except ValidationError as e:
            logger.error(f"Contract detail API validation failed for {contract_id}: {e}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"API-call naar Contract detail {contract_id} mislukt: {e}")
        return None


# ============================================================================
# TRANSFORMATION FUNCTIONS
# ============================================================================

def transform_relatie_list_item_to_input(
    api_relatie: AssuportalRelatieListItem
) -> Optional[RelatieInput]:
    """
    Transformeer een gevalideerd relatie list item naar RelatieInput.

    Args:
        api_relatie: Validated AssuportalRelatieListItem

    Returns:
        Validated RelatieInput of None bij fout
    """
    try:
        email_adressen = [api_relatie.standaard_email] if api_relatie.standaard_email else []

        input_data = {
            'relatie_id': api_relatie.id,
            'hoofdnaam': api_relatie.naam,
            'ts_aangemaakt': convert_invalid_datetime(api_relatie.ts_aangemaakt),
            'email_adressen': email_adressen,
        }

        return RelatieInput(**input_data)
    except ValidationError as e:
        logger.error(f"Relatie {api_relatie.id} transform validation failed: {e}")
        return None


def transform_relatie_detail_to_input(
    api_relatie: AssuportalRelatieDetail
) -> Optional[RelatieInput]:
    """
    Transformeer een gevalideerd relatie detail naar RelatieInput.

    Args:
        api_relatie: Validated AssuportalRelatieDetail

    Returns:
        Validated RelatieInput of None bij fout
    """
    try:
        # Extract all email addresses
        email_adressen = [email.email for email in api_relatie.email_adressen]

        input_data = {
            'relatie_id': api_relatie.id,
            'hoofdnaam': api_relatie.naam,
            'ts_aangemaakt': convert_invalid_datetime(api_relatie.ts_aangemaakt),
            'email_adressen': email_adressen,
        }

        return RelatieInput(**input_data)
    except ValidationError as e:
        logger.error(f"Relatie {api_relatie.id} detail transform validation failed: {e}")
        return None


def transform_contract_to_input(api_contract: AssuportalContract) -> Optional[ContractInput]:
    """
    Transformeer een gevalideerd contract naar ContractInput.

    Args:
        api_contract: Validated AssuportalContract

    Returns:
        Validated ContractInput of None bij fout
    """
    try:
        input_data = {
            'contract_id': api_contract.id,
            'relatie_id': api_contract.relatie_id,
            'polisnummer': api_contract.polisnummer,
            'omschrijving': api_contract.omschrijving,
            'branche': api_contract.branche,
            'datum_ingang': convert_invalid_date(api_contract.datum_ingang),
            'ts_aangemaakt': convert_invalid_datetime(api_contract.ts_aangemaakt),
            'ts_gewijzigd': convert_invalid_datetime(api_contract.ts_gewijzigd),
        }

        return ContractInput(**input_data)
    except ValidationError as e:
        logger.error(f"Contract {api_contract.id} transform validation failed: {e}")
        return None


# ============================================================================
# SAVE FUNCTIONS
# ============================================================================

def merge_email_lists(existing_emails: List[str], new_emails: List[str]) -> List[str]:
    """
    Combineer twee email lijsten, behoud unieke emails (case-insensitive).

    Args:
        existing_emails: Bestaande emails in de database
        new_emails: Nieuwe emails van de API

    Returns:
        Gecombineerde lijst met unieke emails
    """
    # Use lowercase for deduplication, but keep original casing from new_emails (API is authoritative for format)
    seen = set()
    merged = []

    # First add new emails (API is source of truth for formatting)
    for email in new_emails:
        lower = email.lower()
        if lower not in seen:
            seen.add(lower)
            merged.append(email)

    # Then add existing emails that aren't in the new list
    for email in existing_emails:
        lower = email.lower()
        if lower not in seen:
            seen.add(lower)
            merged.append(email)

    return merged


def save_relatie_from_input(
    relatie_input: RelatieInput,
    personen_data: Optional[List[PersoonInput]] = None,
    email_lookup: Optional[Dict[int, str]] = None,
    dry_run: bool = False
) -> Optional[Relaties]:
    """
    Sla een Relatie op vanuit gevalideerde input met MERGE strategie.

    MERGE STRATEGIE: Als een relatie met dit email al bestaat vanuit een AdviesAanvraag
    (relatie_id=None), dan wordt deze relatie ge-upgrade met de API data in plaats van
    een nieuwe aan te maken. Email adressen worden gecombineerd (union).

    Args:
        relatie_input: Validated RelatieInput object
        personen_data: Optional list of validated PersoonInput objects (for detail sync)
        email_lookup: Optional mapping of persoon_id -> email
        dry_run: If True, don't actually save to database

    Returns:
        Relaties object of None bij fout
    """
    try:
        if dry_run:
            logger.info(f"[DRY RUN] Would create/update relatie {relatie_input.relatie_id} ({relatie_input.hoofdnaam})")
            # Return a mock object that counts as success in dry-run
            from types import SimpleNamespace
            return SimpleNamespace(relatie_id=relatie_input.relatie_id, hoofdnaam=relatie_input.hoofdnaam)

        with transaction.atomic():
            # MERGE LOGICA: Check of er al een relatie bestaat
            # Stap 1: Probeer te vinden op relatie_id
            try:
                relatie = Relaties.objects.get(relatie_id=relatie_input.relatie_id)
                # Bestaande API relatie gevonden, update deze
                relatie.hoofdnaam = relatie_input.hoofdnaam
                relatie.ts_aangemaakt = relatie_input.ts_aangemaakt
                # Merge emails: combine existing with API emails
                relatie.email_adressen = merge_email_lists(relatie.email_adressen, relatie_input.email_adressen)
                relatie.save()
                action = "bijgewerkt (bestaande API relatie)"
                logger.info(f"Relatie {relatie_input.relatie_id} ({relatie_input.hoofdnaam}): {action}")

            except Relaties.DoesNotExist:
                # Stap 2: Geen API relatie gevonden, check voor orphaned relatie met dit email
                orphaned_relatie = None
                if relatie_input.email_adressen:
                    for email in relatie_input.email_adressen:
                        # Zoek relatie die:
                        # 1. Nog geen relatie_id heeft (None) - niet gekoppeld aan API
                        # 2. Dit email bevat
                        orphaned_relatie = Relaties.objects.filter(
                            relatie_id__isnull=True,
                            email_adressen__contains=[email]
                        ).first()

                        if orphaned_relatie:
                            logger.info(f"MERGE: Orphaned relatie {orphaned_relatie.pk} matched met API relatie {relatie_input.relatie_id} via email {email}")
                            break

                if orphaned_relatie:
                    # MERGE: Update de orphaned relatie met API data, combine emails
                    existing_emails = orphaned_relatie.email_adressen or []
                    orphaned_relatie.relatie_id = relatie_input.relatie_id
                    orphaned_relatie.hoofdnaam = relatie_input.hoofdnaam
                    orphaned_relatie.ts_aangemaakt = relatie_input.ts_aangemaakt
                    orphaned_relatie.email_adressen = merge_email_lists(existing_emails, relatie_input.email_adressen)
                    orphaned_relatie.save()
                    relatie = orphaned_relatie
                    action = "ge-merged (formulier → API)"
                    logger.info(f"Relatie {relatie_input.relatie_id} ({relatie_input.hoofdnaam}): {action}")
                else:
                    # Geen orphaned relatie gevonden, maak nieuwe aan
                    relatie = Relaties.objects.create(
                        relatie_id=relatie_input.relatie_id,
                        hoofdnaam=relatie_input.hoofdnaam,
                        ts_aangemaakt=relatie_input.ts_aangemaakt,
                        email_adressen=relatie_input.email_adressen,
                    )
                    action = "aangemaakt (nieuwe API relatie)"
                    logger.info(f"Relatie {relatie_input.relatie_id} ({relatie_input.hoofdnaam}): {action}")

            # Als personen data beschikbaar: sla ook Personen op
            if personen_data and email_lookup:
                # Verwijder oude personen (voor re-sync)
                relatie.personen.all().delete()

                # Voeg nieuwe personen toe
                for persoon_input in personen_data:
                    persoon_email = email_lookup.get(persoon_input.api_persoon_id)

                    Personen.objects.create(
                        relatie=relatie,
                        api_persoon_id=persoon_input.api_persoon_id,
                        persoon_naam=persoon_input.persoon_naam,
                        persoon_email=persoon_email
                    )

                logger.debug(f"  → {len(personen_data)} personen opgeslagen")

            return relatie

    except Exception as e:
        logger.error(f"Fout bij opslaan Relatie {relatie_input.relatie_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def save_contract_from_input(
    contract_input: ContractInput,
    dry_run: bool = False
) -> Optional[Contracten]:
    """
    Sla een Contract op vanuit gevalideerde input.

    Args:
        contract_input: Validated ContractInput object
        dry_run: If True, don't actually save to database

    Returns:
        Contracten object of None bij fout
    """
    try:
        # Check of Relatie bestaat
        try:
            relatie = Relaties.objects.get(relatie_id=contract_input.relatie_id)
        except Relaties.DoesNotExist:
            logger.warning(f"Contract {contract_input.contract_id}: Relatie {contract_input.relatie_id} niet gevonden, skip")
            return None

        if dry_run:
            logger.info(f"[DRY RUN] Would create/update contract {contract_input.contract_id} ({contract_input.polisnummer})")
            # Return a mock object that counts as success in dry-run
            from types import SimpleNamespace
            return SimpleNamespace(contract_id=contract_input.contract_id, polisnummer=contract_input.polisnummer)

        with transaction.atomic():
            # Update or create Contract
            contract, created = Contracten.objects.update_or_create(
                contract_id=contract_input.contract_id,
                defaults={
                    'polisnummer': contract_input.polisnummer,
                    'omschrijving': contract_input.omschrijving,
                    'branche': contract_input.branche,
                    'relatie': relatie,
                    'datum_ingang': contract_input.datum_ingang,
                    'ts_aangemaakt': contract_input.ts_aangemaakt,
                    'ts_gewijzigd': contract_input.ts_gewijzigd
                }
            )

            action = "aangemaakt" if created else "bijgewerkt"
            logger.info(f"Contract {contract_input.contract_id} ({contract_input.polisnummer}): {action}")

            return contract

    except Exception as e:
        logger.error(f"Fout bij opslaan Contract {contract_input.contract_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
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

    # Geen match: maak nieuwe Relatie (nog niet gekoppeld aan API)
    logger.info(f"Email {email} niet gevonden, nieuwe Relatie aanmaken")
    relatie = Relaties.objects.create(
        relatie_id=None,  # Nog geen API ID - wordt later via sync gekoppeld
        hoofdnaam=None,
        email_adressen=[email],
    )

    return relatie


# ============================================================================
# MAIN SYNC FUNCTIONS
# ============================================================================

def sync_relaties(
    page_size: int = 50,
    use_detail: bool = False,
    max_pages: Optional[int] = None,
    dry_run: bool = False,
    datum_van: Optional[date] = None,
    datum_tot: Optional[date] = None
) -> Tuple[int, int]:
    """
    Synchroniseer Relaties van Assuportal API naar database met validatie.

    Args:
        page_size: Aantal records per pagina
        use_detail: True om DETAIL endpoint te gebruiken (langzaam maar volledig)
        max_pages: Maximaal aantal paginas (voor testen), None = alle
        dry_run: If True, don't actually save to database
        datum_van: Filter voor relaties aangemaakt/gewijzigd vanaf deze datum (optioneel)
        datum_tot: Filter voor relaties aangemaakt/gewijzigd tot deze datum (optioneel)

    Returns:
        Tuple van (success_count, error_count)
    """
    filter_msg = ""
    if datum_van or datum_tot:
        filter_msg = f" [filter: {datum_van or 'begin'} tot {datum_tot or 'eind'}]"
    logger.info(f"=== Start Relaties synchronisatie {'(DRY RUN)' if dry_run else ''}{filter_msg} ===")

    success_count = 0
    error_count = 0
    page = 1

    # Define the processing logic
    def process_pages():
        nonlocal success_count, error_count, page

        while True:
            # Stop als max_pages bereikt
            if max_pages and page > max_pages:
                logger.info(f"Max pages ({max_pages}) bereikt, stoppen")
                break

            # Haal lijst op met validatie
            response = fetch_relaties_list(
                page=page,
                size=page_size,
                datum_van=datum_van,
                datum_tot=datum_tot
            )

            if not response or response.result != 'ok':
                logger.error(f"Geen geldige response voor pagina {page}")
                break

            data_list = response.data
            meta = response.meta or {}

            if not data_list:
                logger.info(f"Geen data op pagina {page}, stoppen")
                break

            logger.info(f"Pagina {page}/{meta.get('last_page', '?')}: {len(data_list)} relaties")

            # Verwerk elke relatie
            for relatie_data in data_list:
                relatie_id = relatie_data.id

                # Als use_detail: haal volledige data op
                if use_detail:
                    detail_response = fetch_relatie_detail(relatie_id)
                    if detail_response and detail_response.result == 'ok':
                        # Transform detail to input
                        relatie_input = transform_relatie_detail_to_input(detail_response.data)

                        if relatie_input:
                            # Prepare personen data
                            personen_list = []
                            email_lookup = {}

                            # Build email lookup
                            for email_obj in detail_response.data.email_adressen:
                                if email_obj.persoon_id and email_obj.email:
                                    email_lookup[email_obj.persoon_id] = email_obj.email

                            # Transform personen
                            for persoon in detail_response.data.personen:
                                # Skip persons with empty names (corrupted data)
                                if not persoon.naam or not persoon.naam.strip():
                                    logger.warning(f"Skipping persoon {persoon.id} in relatie {relatie_id}: empty name")
                                    continue

                                try:
                                    persoon_input = PersoonInput(
                                        api_persoon_id=persoon.id,
                                        persoon_naam=persoon.naam,
                                        persoon_email=email_lookup.get(persoon.id)
                                    )
                                    personen_list.append(persoon_input)
                                except ValidationError as e:
                                    logger.error(f"Persoon {persoon.id} validation failed: {e}")

                            result = save_relatie_from_input(
                                relatie_input,
                                personen_data=personen_list,
                                email_lookup=email_lookup,
                                dry_run=dry_run
                            )
                        else:
                            result = None
                    else:
                        logger.error(f"Kon detail niet ophalen voor Relatie {relatie_id}")
                        result = None
                else:
                    # Gebruik LIST data
                    relatie_input = transform_relatie_list_item_to_input(relatie_data)
                    if relatie_input:
                        result = save_relatie_from_input(relatie_input, dry_run=dry_run)
                    else:
                        result = None

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

    if dry_run:
        # Don't use transaction for dry run
        process_pages()
    else:
        # Wrap everything in a transaction - all or nothing
        try:
            with transaction.atomic():
                process_pages()
        except Exception as e:
            logger.error(f"CRITICAL: Relaties sync transaction failed, rolling back: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0, 1

    logger.info(f"=== Relaties sync voltooid: {success_count} succesvol, {error_count} fouten ===")
    return success_count, error_count


def sync_contracten(
    page_size: int = 50,
    use_detail: bool = True,
    max_pages: Optional[int] = None,
    dry_run: bool = False,
    datum_van: Optional[date] = None,
    datum_tot: Optional[date] = None
) -> Tuple[int, int, int]:
    """
    Synchroniseer Contracten van Assuportal API naar database met validatie.

    Args:
        page_size: Aantal records per pagina
        use_detail: True om DETAIL endpoint te gebruiken (langzaam maar volledig met branche, datum_ingang, omschrijving)
        max_pages: Maximaal aantal paginas (voor testen), None = alle
        dry_run: If True, don't actually save to database
        datum_van: Filter voor contracten aangemaakt/gewijzigd vanaf deze datum (optioneel)
        datum_tot: Filter voor contracten aangemaakt/gewijzigd tot deze datum (optioneel)

    Returns:
        Tuple van (success_count, error_count, skipped_count)
    """
    filter_msg = ""
    if datum_van or datum_tot:
        filter_msg = f" [filter: {datum_van or 'begin'} tot {datum_tot or 'eind'}]"
    logger.info(f"=== Start Contracten synchronisatie {'(DRY RUN)' if dry_run else ''}{filter_msg} ===")

    success_count = 0
    error_count = 0
    skipped_count = 0
    page = 1

    # Define the processing logic
    def process_pages():
        nonlocal success_count, error_count, skipped_count, page

        while True:
            # Stop als max_pages bereikt
            if max_pages and page > max_pages:
                logger.info(f"Max pages ({max_pages}) bereikt, stoppen")
                break

            # Haal lijst op met validatie
            response = fetch_contracten_list(
                page=page,
                size=page_size,
                datum_van=datum_van,
                datum_tot=datum_tot
            )

            if not response or response.result != 'ok':
                logger.error(f"Geen geldige response voor pagina {page}")
                break

            data_list = response.data
            meta = response.meta or {}

            if not data_list:
                logger.info(f"Geen data op pagina {page}, stoppen")
                break

            logger.info(f"Pagina {page}/{meta.get('last_page', '?')}: {len(data_list)} contracten")

            # Verwerk elk contract
            for contract_data in data_list:
                contract_id = contract_data.id

                # Als use_detail: haal volledige data op
                if use_detail:
                    detail_response = fetch_contract_detail(contract_id)
                    if detail_response and detail_response.result == 'ok':
                        # Transform detail to input
                        contract_input = transform_contract_to_input(detail_response.data)
                    else:
                        logger.error(f"Kon detail niet ophalen voor Contract {contract_id}")
                        contract_input = None
                else:
                    # Gebruik LIST data
                    contract_input = transform_contract_to_input(contract_data)

                if not contract_input:
                    error_count += 1
                    continue

                # Save contract
                result = save_contract_from_input(contract_input, dry_run=dry_run)

                if result:
                    success_count += 1
                elif result is None and contract_data.relatie_id:
                    # None betekent Relatie niet gevonden (zie save_contract_from_input)
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

    if dry_run:
        # Don't use transaction for dry run
        process_pages()
    else:
        # Wrap everything in a transaction - all or nothing
        try:
            with transaction.atomic():
                process_pages()
        except Exception as e:
            logger.error(f"CRITICAL: Contracten sync transaction failed, rolling back: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0, 0, 0

    logger.info(f"=== Contracten sync voltooid: {success_count} succesvol, {error_count} fouten, {skipped_count} geskipt ===")
    return success_count, error_count, skipped_count
