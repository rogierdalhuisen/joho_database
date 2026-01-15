import requests
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, date
from django.db import transaction
from decouple import config
from pydantic import ValidationError

from .models import Relaties, AdviesAanvragen
from .api_assuportal import find_or_create_relatie_by_email
from .schemas_egrip import (
    EgripAPIResponse,
    EgripResult,
    AdviesAanvraagInput,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CONFIGURATION
# ============================================================================

def get_egrip_config():
    """Haal E-grip API configuratie op."""
    return {
        'endpoint': config('EGRIP_ENDPOINT'),
        'token': config('EGRIP_BEARER_TOKEN')
    }


# ============================================================================
# POSITION TO FIELD MAPPING
# ============================================================================

# Complete mapping van E-grip position → AdviesAanvragen veldnaam
POSITION_TO_FIELD_MAP = {
    # Persoonlijke gegevens hoofdverzekerde
    20: 'advies_voor_mezelf',
    50: 'aanhef',
    60: 'voorletters_roepnaam',
    70: 'achternaam',
    80: 'geboortedatum',  # DATE
    90: 'land_nationaliteit',
    100: 'email',  # REQUIRED
    110: 'telefoonnummer',
    120: 'vaste_woonplaats',
    130: 'geen_vaste_woonplaats',  # BOOLEAN

    # Meerdere verzekerden
    140: 'meerdere_verzekerden',
    141: 'partner_naam',
    142: 'partner_geboortedatum',  # DATE
    143: 'partner_nationaliteit',
    144: 'kind1_naam',
    145: 'kind1_geboortedatum',  # DATE
    146: 'kind1_nationaliteit',
    147: 'kind2_naam',
    148: 'kind2_geboortedatum',  # DATE
    149: 'kind2_nationaliteit',
    150: 'kind3_naam',
    151: 'kind3_geboortedatum',  # DATE
    152: 'kind3_nationaliteit',
    153: 'kind4_naam',
    154: 'kind4_geboortedatum',  # DATE
    155: 'kind4_nationaliteit',
    159: 'anders_personen',

    # Situatie en plannen
    165: 'situatie_type',
    170: 'bestemming_land',
    175: 'vertrekdatum',  # DATE
    220: 'uitschrijven_brp',
    225: 'huidig_woonland',
    230: 'advies_voor',
    240: 'hoofdreden_verblijf',
    245: 'toelichting_hoofdreden',
    247: 'verwachte_duur_verblijf',
    248: 'toelichting_duur',

    # Werk en inkomen
    250: 'werk_omschrijving',
    260: 'plannen_omschrijving',
    270: 'salaris_uit_nederland',

    # Arbeidsongeschiktheidsverzekering
    280: 'interesse_aov',
    290: 'loondienst_of_zelfstandig',
    300: 'eigen_onderneming_3jaar',
    310: 'bruto_jaarinkomen',
    320: 'aov_geen_offerte_reden',
    330: 'loon_doorbetaald_bij_ziekte',
    340: 'toelichting_uitkering',
    350: 'bruto_salaris_inkomen',
    360: 'salaris_per_maand_jaar',
    370: 'bouwplaats_of_offshore',
    380: 'bouwplaats_hoe_vaak',
    390: 'gevaarlijke_stoffen',
    400: 'toelichting_gevaarlijke_stoffen',
    411: 'interesse_internationale_aov',
    412: 'geen_interesse_aov_reden',
    413: 'functieomschrijving',
    414: 'type_werkzaamheden',
    415: 'verwacht_inkomen',
    416: 'inkomen_toelichting',

    # Ziektekostenverzekering
    419: 'interesse_zkv',
    420: 'zkv_geen_interesse_reden',
    430: 'zkv_dekkingsvariant',
    440: 'zkv_eigen_risico_voorkeur',
    450: 'zkv_eigen_risico_bedrag',
    460: 'zkv_periode',
    470: 'zkv_periode_omschrijving_motivatie',
    480: 'zkv_periode_omschrijving',
    490: 'huidige_verzekeraar',
    500: 'voorkeur_verzekeraar',
    510: 'medische_bijzonderheden',
    520: 'medische_bijzonderheden_toelichting',
    530: 'specifieke_wensen_zkv',
    540: 'wensen_toelichting',
    550: 'dekking_zwangerschap',
    560: 'zwangerschap_toelichting',

    # Aanvullende verzekeringen
    565: 'andere_verzekeringen_interesse',
    566: 'overlijdensrisico_bedrag',
    567: 'overlijdensrisico_bedrag_anders',
    568: 'overlijdensrisico_bestemming',
    569: 'overlijdensrisico_bestemming_anders',

    # Sporten en activiteiten
    580: 'sporten_activiteiten',
    590: 'sport_semiprofessioneel',
    600: 'sport_professioneel_omschrijving',

    # Huis in Nederland
    660: 'huis_in_nederland',
    670: 'huis_type',
    680: 'woning_verhuurd',
    690: 'woning_eigen_gebruik',
    700: 'woning_verblijf_frequentie',
    710: 'woning_opmerkingen',

    # Marketing en contact
    740: 'hoe_gevonden',
    750: 'welke_website',
    760: 'naam_werkgever',
    770: 'hoe_gevonden_overig',
    780: 'eerder_contact_joho',
    790: 'eerder_contact_keuze',
    800: 'naam_contactpersoon',
    810: 'eerder_contact_anders',
    820: 'advies_vorm',
}

# Velden die datum conversie nodig hebben
DATE_FIELDS = {
    'geboortedatum', 'vertrekdatum', 'partner_geboortedatum',
    'kind1_geboortedatum', 'kind2_geboortedatum',
    'kind3_geboortedatum', 'kind4_geboortedatum'
}

# Velden die boolean conversie nodig hebben
BOOLEAN_FIELDS = {
    'geen_vaste_woonplaats'
}


# ============================================================================
# API FETCH FUNCTIONS
# ============================================================================

def fetch_egrip_form_data(form_id: str = '2') -> Optional[EgripAPIResponse]:
    """
    Haal volledige form data op van E-grip API met Pydantic validatie.

    Args:
        form_id: Het formulier ID (default '2')

    Returns:
        Validated EgripAPIResponse of None bij fout
    """
    config_data = get_egrip_config()

    if not config_data['endpoint'] or not config_data['token']:
        logger.critical("EGRIP_ENDPOINT of EGRIP_BEARER_TOKEN niet geconfigureerd in .env")
        return None

    headers = {
        'Authorization': f"Bearer {config_data['token']}",
        'Content-Type': 'application/json'
    }

    params = {'formId': form_id}

    try:
        logger.info(f"Fetching E-grip form {form_id}...")
        response = requests.get(
            config_data['endpoint'],
            headers=headers,
            params=params,
            timeout=30
        )
        response.raise_for_status()
        raw_data = response.json()

        # Validate with Pydantic
        try:
            validated_data = EgripAPIResponse(**raw_data)
            results_count = len(validated_data.results)
            logger.info(f"✓ E-grip API success: {results_count} results ontvangen en gevalideerd")
            return validated_data
        except ValidationError as e:
            logger.error(f"E-grip API response validation failed: {e}")
            logger.error(f"Raw response (first 500 chars): {str(raw_data)[:500]}")
            return None

    except requests.exceptions.RequestException as e:
        logger.error(f"E-grip API call failed: {e}")
        return None


# ============================================================================
# DATA EXTRACTION & CONVERSION
# ============================================================================

def parse_date_value(value: str) -> Optional[date]:
    """
    Parse datum in DD-MM-YYYY formaat.

    Args:
        value: Datum string (bijv. "28-06-1961")

    Returns:
        date object of None
    """
    if not value or value in ['- Maak een keuze -', '0000-00-00', '']:
        return None

    try:
        return datetime.strptime(value, '%d-%m-%Y').date()
    except (ValueError, TypeError):
        logger.warning(f"Kon datum niet parsen: {value}")
        return None


def parse_boolean_value(value: str) -> Optional[bool]:
    """
    Convert "Ja"/"Nee" naar Boolean.

    Args:
        value: String zoals "Ja", "Nee", "Yes", "No"

    Returns:
        True, False of None
    """
    if not value:
        return None

    value_lower = value.lower().strip()

    if value_lower in ['ja', 'yes', '1']:
        return True
    if value_lower in ['nee', 'no', 'neen', '0']:
        return False

    return None


def parse_datetime_iso(datetime_string: str) -> Optional[datetime]:
    """
    Parse ISO datetime string van E-grip API.

    Args:
        datetime_string: ISO format (bijv. "2026-01-08T14:26:14+01:00")

    Returns:
        datetime object (timezone-aware) of None
    """
    if not datetime_string:
        return None

    try:
        # Handle various timezone formats
        dt_str = datetime_string.replace('+01:00', '+00:00').replace('+02:00', '+00:00')
        return datetime.fromisoformat(dt_str)
    except (ValueError, TypeError) as e:
        logger.warning(f"Kon datetime niet parsen: {datetime_string} - {e}")
        return None


def transform_egrip_result_to_input(result: EgripResult) -> Optional[AdviesAanvraagInput]:
    """
    Transformeer een gevalideerd EgripResult naar AdviesAanvraagInput.

    Args:
        result: Validated EgripResult object

    Returns:
        Validated AdviesAanvraagInput of None bij fout
    """
    try:
        # Build answer lookup: position -> value
        answers = {f.position: f.value for f in result.fields}

        # Extract email (REQUIRED)
        email = answers.get(100)
        if not email:
            logger.warning(f"Result {result.resultId}: Geen email (pos 100), skip")
            return None

        # Parse metadata
        submitted_at = parse_datetime_iso(result.dateSubmitted)
        if not submitted_at:
            submitted_at = datetime.now()  # Fallback

        # Build input data dictionary
        input_data = {
            'external_result_id': result.resultId,
            'form_id': result.formId,
            'email': email,
            'ingediend_op': submitted_at,
            'referral_source': result.referral.source if result.referral else None,
            'referral_medium': result.referral.medium if result.referral else None,
            'referral_campaign': result.referral.campaign if result.referral else None,
            'raw_form_data': result.model_dump(),  # Backup
        }

        # Map alle positions naar velden
        for position, field_name in POSITION_TO_FIELD_MAP.items():
            value = answers.get(position)

            # Skip lege waardes en "- Maak een keuze -"
            if not value or value == '- Maak een keuze -':
                continue

            # Special handling voor datum velden
            if field_name in DATE_FIELDS:
                value = parse_date_value(value)

            # Special handling voor boolean velden
            elif field_name in BOOLEAN_FIELDS:
                value = parse_boolean_value(value)

            # Sla op (skip None waardes)
            if value is not None:
                input_data[field_name] = value

        # Validate with Pydantic
        try:
            validated_input = AdviesAanvraagInput(**input_data)
            return validated_input
        except ValidationError as e:
            logger.error(f"Result {result.resultId}: Validation failed: {e}")
            return None

    except Exception as e:
        logger.error(f"Result {result.resultId}: Transform failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ============================================================================
# SAVE FUNCTION
# ============================================================================

def save_aanvraag_from_input(
    validated_input: AdviesAanvraagInput,
    dry_run: bool = False
) -> Optional[AdviesAanvragen]:
    """
    Sla één AdviesAanvraag op vanuit gevalideerde input.

    Args:
        validated_input: Validated AdviesAanvraagInput object
        dry_run: If True, don't actually save to database

    Returns:
        AdviesAanvragen object of None bij fout/skip
    """
    try:
        result_id = validated_input.external_result_id

        # Check duplicate
        if AdviesAanvragen.objects.filter(external_result_id=result_id).exists():
            logger.debug(f"Result {result_id} al geïmporteerd, skip")
            return None

        if dry_run:
            logger.info(f"[DRY RUN] Would create aanvraag {result_id} for {validated_input.email}")
            # Return a mock object that counts as success in dry-run
            from types import SimpleNamespace
            return SimpleNamespace(external_result_id=result_id, email=validated_input.email)

        with transaction.atomic():
            # Find or create Relatie
            relatie = find_or_create_relatie_by_email(validated_input.email)

            # Update relatie stamgegevens als nog niet gekoppeld aan API
            if relatie.relatie_id is None and not relatie.hoofdnaam:
                voornaam = validated_input.voorletters_roepnaam or ''
                achternaam = validated_input.achternaam or ''
                if voornaam or achternaam:
                    relatie.hoofdnaam = f"{voornaam} {achternaam}".strip()
                    relatie.save()

            # Convert Pydantic model to dict, excluding None values
            aanvraag_data = validated_input.model_dump(exclude_none=True)

            # Add relatie (not in Pydantic model)
            aanvraag_data['relatie'] = relatie

            # Create aanvraag
            aanvraag = AdviesAanvragen.objects.create(**aanvraag_data)

            naam = f"{aanvraag.voorletters_roepnaam or ''} {aanvraag.achternaam or ''}".strip()
            logger.info(f"✓ Aanvraag {result_id} opgeslagen: {naam} ({validated_input.email})")
            return aanvraag

    except Exception as e:
        logger.error(f"✗ Fout bij opslaan aanvraag {validated_input.external_result_id}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


# ============================================================================
# MAIN SYNC FUNCTION
# ============================================================================

def sync_egrip_formulieren(
    form_id: str = '2',
    max_results: Optional[int] = None,
    dry_run: bool = False
) -> Tuple[int, int, int]:
    """
    Synchroniseer E-grip formulier data naar database met volledige validatie.

    Args:
        form_id: Het formulier ID (default '2')
        max_results: Maximaal aantal results (voor testen), None = alle
        dry_run: If True, don't actually save to database

    Returns:
        Tuple van (success_count, error_count, skipped_count)
    """
    logger.info(f"=== Start E-grip sync voor form {form_id} {'(DRY RUN)' if dry_run else ''} ===")

    # Fetch and validate data
    validated_response = fetch_egrip_form_data(form_id)

    if not validated_response:
        logger.error("Geen geldige data ontvangen van E-grip API")
        return 0, 1, 0

    results = validated_response.results

    if not results:
        logger.warning("Geen results in API response")
        return 0, 0, 0

    # Limit voor testen
    if max_results:
        results = results[:max_results]
        logger.info(f"TEST MODE: Verwerk alleen eerste {max_results} van {len(validated_response.results)} results")

    success_count = 0
    error_count = 0
    skipped_count = 0

    # Wrap entire sync in transaction for atomicity (unless dry_run)
    def process_results():
        nonlocal success_count, error_count, skipped_count

        for idx, result in enumerate(results, 1):
            result_id = result.resultId
            logger.debug(f"Verwerk result {idx}/{len(results)}: {result_id}")

            # Transform to validated input
            validated_input = transform_egrip_result_to_input(result)

            if not validated_input:
                error_count += 1
                continue

            # Save to database
            aanvraag = save_aanvraag_from_input(validated_input, dry_run=dry_run)

            if aanvraag:
                success_count += 1
            elif aanvraag is None:
                skipped_count += 1

    if dry_run:
        # Don't use transaction for dry run
        process_results()
    else:
        # Wrap everything in a transaction - all or nothing
        try:
            with transaction.atomic():
                process_results()
        except Exception as e:
            logger.error(f"CRITICAL: Sync transaction failed, rolling back all changes: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return 0, 1, 0

    logger.info(f"=== E-grip sync compleet: {success_count} succesvol, {skipped_count} geskipt, {error_count} fouten ===")
    return success_count, error_count, skipped_count
