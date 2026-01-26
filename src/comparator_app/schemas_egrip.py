"""
Pydantic schemas for E-grip API validation.

These schemas validate all incoming API data before it touches the database,
ensuring data integrity and providing clear error messages.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional, Dict, Any
from datetime import datetime, date


class EgripField(BaseModel):
    """A single field from an E-grip form submission."""

    position: int = Field(..., ge=0, description="Field position number")
    value: str = Field(..., description="Field value")

    model_config = ConfigDict(extra='ignore')


class EgripReferral(BaseModel):
    """Referral information from form submission."""

    source: Optional[str] = None
    medium: Optional[str] = None
    campaign: Optional[str] = None

    model_config = ConfigDict(extra='ignore')


class EgripResult(BaseModel):
    """Complete E-grip form submission result."""

    resultId: str = Field(..., min_length=1, description="Unique result identifier")
    formId: str | int = Field(..., description="Form identifier (can be string or int)")
    dateSubmitted: str = Field(..., description="Submission datetime (ISO format)")
    fields: List[EgripField] = Field(default_factory=list, description="Form field data")
    referral: Optional[EgripReferral] = None

    model_config = ConfigDict(extra='ignore', coerce_numbers_to_str=True)

    @field_validator('formId', mode='before')
    @classmethod
    def coerce_form_id_to_string(cls, v) -> str:
        """Convert formId to string if it's an integer."""
        return str(v)

    @field_validator('resultId')
    @classmethod
    def validate_result_id(cls, v: str) -> str:
        """Ensure result ID is valid."""
        if not v or len(v.strip()) < 3:
            raise ValueError('Result ID must be at least 3 characters')
        return v.strip()

    @field_validator('dateSubmitted')
    @classmethod
    def validate_date_submitted(cls, v: str) -> str:
        """Validate ISO datetime format."""
        if not v:
            raise ValueError('dateSubmitted cannot be empty')
        # Try to parse it to ensure it's valid
        try:
            # Handle various ISO formats
            if '+' in v or 'Z' in v:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            else:
                datetime.fromisoformat(v)
        except (ValueError, AttributeError):
            raise ValueError(f'Invalid ISO datetime format: {v}')
        return v


class EgripAPIResponse(BaseModel):
    """Complete E-grip API response."""

    formId: str | int
    results: List[EgripResult] = Field(default_factory=list)
    fields: Optional[List[Dict[str, Any]]] = None  # Field definitions (not used for sync)

    model_config = ConfigDict(extra='ignore')

    @field_validator('formId', mode='before')
    @classmethod
    def coerce_form_id_to_string(cls, v) -> str:
        """Convert formId to string if it's an integer."""
        return str(v)


class AdviesAanvraagInput(BaseModel):
    """
    Validated input data for creating an AdviesAanvraag.

    This schema represents the cleaned, validated data extracted from
    an E-grip form submission, ready for database insertion.
    """

    # Core identification
    external_result_id: str = Field(..., min_length=1, max_length=255)
    form_id: str = Field(..., max_length=50)
    email: EmailStr
    ingediend_op: datetime

    # Referral metadata
    referral_source: Optional[str] = Field(None, max_length=255)
    referral_medium: Optional[str] = Field(None, max_length=255)
    referral_campaign: Optional[str] = Field(None, max_length=500)

    # Personal info
    advies_voor_mezelf: Optional[str] = Field(None, max_length=255)
    aanhef: Optional[str] = Field(None, max_length=50)
    voorletters_roepnaam: Optional[str] = Field(None, max_length=255)
    achternaam: Optional[str] = Field(None, max_length=255)
    geboortedatum: Optional[date] = None
    land_nationaliteit: Optional[str] = Field(None, max_length=255)
    telefoonnummer: Optional[str] = Field(None, max_length=100)
    vaste_woonplaats: Optional[str] = Field(None, max_length=500)
    geen_vaste_woonplaats: Optional[bool] = None

    # Multiple insured persons
    meerdere_verzekerden: Optional[str] = Field(None, max_length=500)
    partner_naam: Optional[str] = Field(None, max_length=255)
    partner_geboortedatum: Optional[date] = None
    partner_nationaliteit: Optional[str] = Field(None, max_length=255)
    kind1_naam: Optional[str] = Field(None, max_length=255)
    kind1_geboortedatum: Optional[date] = None
    kind1_nationaliteit: Optional[str] = Field(None, max_length=255)
    kind2_naam: Optional[str] = Field(None, max_length=255)
    kind2_geboortedatum: Optional[date] = None
    kind2_nationaliteit: Optional[str] = Field(None, max_length=255)
    kind3_naam: Optional[str] = Field(None, max_length=255)
    kind3_geboortedatum: Optional[date] = None
    kind3_nationaliteit: Optional[str] = Field(None, max_length=255)
    kind4_naam: Optional[str] = Field(None, max_length=255)
    kind4_geboortedatum: Optional[date] = None
    kind4_nationaliteit: Optional[str] = Field(None, max_length=255)
    anders_personen: Optional[str] = None

    # Situation and plans
    situatie_type: Optional[str] = Field(None, max_length=500)
    bestemming_land: Optional[str] = Field(None, max_length=255)
    vertrekdatum: Optional[date] = None
    uitschrijven_brp: Optional[str] = Field(None, max_length=255)
    huidig_woonland: Optional[str] = Field(None, max_length=255)
    advies_voor: Optional[str] = Field(None, max_length=500)
    hoofdreden_verblijf: Optional[str] = Field(None, max_length=500)
    toelichting_hoofdreden: Optional[str] = None
    verwachte_duur_verblijf: Optional[str] = Field(None, max_length=255)
    toelichting_duur: Optional[str] = None

    # Work and income
    werk_omschrijving: Optional[str] = None
    plannen_omschrijving: Optional[str] = None
    salaris_uit_nederland: Optional[str] = Field(None, max_length=255)

    # Disability insurance (AOV)
    interesse_aov: Optional[str] = Field(None, max_length=255)
    loondienst_of_zelfstandig: Optional[str] = Field(None, max_length=255)
    eigen_onderneming_3jaar: Optional[str] = Field(None, max_length=255)
    bruto_jaarinkomen: Optional[str] = Field(None, max_length=255)
    aov_geen_offerte_reden: Optional[str] = None
    loon_doorbetaald_bij_ziekte: Optional[str] = Field(None, max_length=500)
    toelichting_uitkering: Optional[str] = None
    bruto_salaris_inkomen: Optional[str] = Field(None, max_length=255)
    salaris_per_maand_jaar: Optional[str] = Field(None, max_length=255)
    bouwplaats_of_offshore: Optional[str] = Field(None, max_length=255)
    bouwplaats_hoe_vaak: Optional[str] = Field(None, max_length=255)
    gevaarlijke_stoffen: Optional[str] = Field(None, max_length=255)
    toelichting_gevaarlijke_stoffen: Optional[str] = None
    interesse_internationale_aov: Optional[str] = None
    geen_interesse_aov_reden: Optional[str] = None
    functieomschrijving: Optional[str] = Field(None, max_length=500)
    type_werkzaamheden: Optional[str] = Field(None, max_length=255)
    verwacht_inkomen: Optional[str] = Field(None, max_length=255)
    inkomen_toelichting: Optional[str] = None

    # Health insurance (ZKV)
    interesse_zkv: Optional[str] = Field(None, max_length=255)
    zkv_geen_interesse_reden: Optional[str] = None
    zkv_dekkingsvariant: Optional[str] = Field(None, max_length=255)
    zkv_eigen_risico_voorkeur: Optional[str] = Field(None, max_length=255)
    zkv_eigen_risico_bedrag: Optional[str] = Field(None, max_length=255)
    zkv_periode: Optional[str] = Field(None, max_length=255)
    zkv_periode_omschrijving_motivatie: Optional[str] = None
    zkv_periode_omschrijving: Optional[str] = None
    huidige_verzekeraar: Optional[str] = Field(None, max_length=255)
    voorkeur_verzekeraar: Optional[str] = Field(None, max_length=255)
    medische_bijzonderheden: Optional[str] = Field(None, max_length=255)
    medische_bijzonderheden_toelichting: Optional[str] = None
    specifieke_wensen_zkv: Optional[str] = Field(None, max_length=255)
    wensen_toelichting: Optional[str] = None
    dekking_zwangerschap: Optional[str] = Field(None, max_length=255)
    zwangerschap_toelichting: Optional[str] = None

    # Additional insurances
    andere_verzekeringen_interesse: Optional[str] = None
    overlijdensrisico_bedrag: Optional[str] = Field(None, max_length=255)
    overlijdensrisico_bedrag_anders: Optional[str] = Field(None, max_length=255)
    overlijdensrisico_bestemming: Optional[str] = None
    overlijdensrisico_bestemming_anders: Optional[str] = None

    # Sports and activities
    sporten_activiteiten: Optional[str] = None
    sport_semiprofessioneel: Optional[str] = Field(None, max_length=255)
    sport_professioneel_omschrijving: Optional[str] = None

    # House in Netherlands
    huis_in_nederland: Optional[str] = Field(None, max_length=255)
    huis_type: Optional[str] = Field(None, max_length=255)
    woning_verhuurd: Optional[str] = Field(None, max_length=255)
    woning_eigen_gebruik: Optional[str] = Field(None, max_length=255)
    woning_verblijf_frequentie: Optional[str] = Field(None, max_length=500)
    woning_opmerkingen: Optional[str] = None

    # Marketing and contact
    hoe_gevonden: Optional[str] = Field(None, max_length=255)
    welke_website: Optional[str] = Field(None, max_length=500)
    naam_werkgever: Optional[str] = Field(None, max_length=500)
    hoe_gevonden_overig: Optional[str] = None
    eerder_contact_joho: Optional[str] = Field(None, max_length=255)
    eerder_contact_keuze: Optional[str] = Field(None, max_length=255)
    naam_contactpersoon: Optional[str] = Field(None, max_length=500)
    eerder_contact_anders: Optional[str] = None
    advies_vorm: Optional[str] = Field(None, max_length=255)

    # Raw backup
    raw_form_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(extra='forbid')  # Reject unknown fields

    @field_validator('geboortedatum', 'partner_geboortedatum',
                     'kind1_geboortedatum', 'kind2_geboortedatum',
                     'kind3_geboortedatum', 'kind4_geboortedatum')
    @classmethod
    def validate_birth_dates(cls, v: Optional[date]) -> Optional[date]:
        """Validate birthdates - log warnings for suspicious data but keep it."""
        if v is None:
            return v

        import logging
        logger = logging.getLogger(__name__)
        today = date.today()

        # Birthdates shouldn't be in the future - but keep the data with warning
        if v > today:
            logger.warning(f'Birthdate {v} is in the future - keeping as-is but likely incorrect')

        # Sanity check: not before 1900 - warn but keep
        if v.year < 1900:
            logger.warning(f'Birthdate {v} seems invalid (before 1900) - keeping as-is but likely incorrect')

        return v

    @field_validator('vertrekdatum')
    @classmethod
    def validate_departure_date(cls, v: Optional[date]) -> Optional[date]:
        """Validate departure date - log warnings for suspicious data but keep it."""
        if v is None:
            return v

        import logging
        logger = logging.getLogger(__name__)
        today = date.today()

        # Allow future dates (people plan to travel)
        # But sanity check: not more than 5 years in future - warn but keep
        from datetime import timedelta
        max_future = today + timedelta(days=365 * 5)
        if v > max_future:
            logger.warning(f'Departure date {v} is unreasonably far in future (>5 years) - keeping as-is but likely incorrect')

        # Sanity check: not before 2000 - warn but keep
        if v.year < 2000:
            logger.warning(f'Departure date {v} seems invalid (before 2000) - keeping as-is, possibly data entry error')

        return v

    @field_validator('email')
    @classmethod
    def validate_email_not_test(cls, v: str) -> str:
        """Warn about test emails but allow them."""
        if any(test in v.lower() for test in ['test@', 'example@', 'noreply@']):
            # Log warning but don't reject
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Test/example email detected: {v}")
        return v
