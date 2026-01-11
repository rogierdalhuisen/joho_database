"""
Pydantic schemas for Assuportal API validation.

These schemas validate all incoming API data before it touches the database,
ensuring data integrity and providing clear error messages.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ConfigDict
from typing import List, Optional
from datetime import datetime, date


class AssuportalEmailAddress(BaseModel):
    """Email address linked to a person."""

    email: str  # Changed from EmailStr to allow invalid emails from API
    persoon_id: Optional[int] = None

    model_config = ConfigDict(extra='ignore')

    @field_validator('email')
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        """Validate email format but allow invalid emails with warning."""
        if '@' not in v or '.' not in v:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid email format in API data: '{v}' - keeping as-is")

        return v


class AssuportalPersoon(BaseModel):
    """Person data from Assuportal API."""

    id: int = Field(..., ge=1)
    naam: str = Field(..., min_length=1)

    model_config = ConfigDict(extra='ignore')

    @field_validator('naam')
    @classmethod
    def validate_naam(cls, v: str) -> str:
        """Ensure name is not empty after stripping."""
        stripped = v.strip()
        if not stripped:
            raise ValueError('Person name cannot be empty')
        return stripped


class AssuportalRelatieListItem(BaseModel):
    """Relatie data from LIST endpoint (minimal data)."""

    id: int = Field(..., ge=1, description="Relatie ID from Assuportal")
    naam: str = Field(..., min_length=1, description="Relatie name")
    standaard_email: Optional[str] = Field(None, description="Primary email (may be invalid)")
    ts_aangemaakt: Optional[str] = Field(None, description="Creation timestamp")

    model_config = ConfigDict(extra='ignore')

    @field_validator('standaard_email')
    @classmethod
    def validate_email_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate email format but allow invalid emails with warning."""
        if not v:
            return v

        # Basic check for email format
        if '@' not in v or '.' not in v:
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Invalid email format in API data: '{v}' - keeping as-is")

        return v

    @field_validator('ts_aangemaakt')
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate timestamp format and reject invalid dates."""
        if not v or v in ['0000-00-00 00:00:00', '', '0000-00-00']:
            return None

        # Try to parse it
        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            raise ValueError(f'Invalid timestamp format: {v}')

        return v


class AssuportalRelatieDetail(BaseModel):
    """Relatie data from DETAIL endpoint (complete data with personen)."""

    id: int = Field(..., ge=1)
    naam: str = Field(..., min_length=1)
    ts_aangemaakt: Optional[str] = None
    personen: List[AssuportalPersoon] = Field(default_factory=list)
    email_adressen: List[AssuportalEmailAddress] = Field(default_factory=list)

    model_config = ConfigDict(extra='ignore')

    @field_validator('ts_aangemaakt')
    @classmethod
    def validate_timestamp(cls, v: Optional[str]) -> Optional[str]:
        """Validate timestamp format."""
        if not v or v in ['0000-00-00 00:00:00', '', '0000-00-00']:
            return None

        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            raise ValueError(f'Invalid timestamp format: {v}')

        return v


class AssuportalRelatiesAPIResponse(BaseModel):
    """Complete API response for Relaties LIST endpoint."""

    result: str = Field(..., pattern='^ok$')
    data: List[AssuportalRelatieListItem] = Field(default_factory=list)
    meta: Optional[dict] = None

    model_config = ConfigDict(extra='ignore')


class AssuportalRelatieDetailAPIResponse(BaseModel):
    """Complete API response for Relatie DETAIL endpoint."""

    result: str = Field(..., pattern='^ok$')
    data: AssuportalRelatieDetail

    model_config = ConfigDict(extra='ignore')


class AssuportalContract(BaseModel):
    """Contract data from Assuportal API."""

    id: int = Field(..., ge=1, description="Contract ID")
    relatie_id: int = Field(..., ge=1, description="Related Relatie ID")
    polisnummer: str = Field(default='', description="Policy number")
    branche: Optional[str] = None
    datum_ingang: Optional[str] = None
    ts_aangemaakt: Optional[str] = None
    ts_gewijzigd: Optional[str] = None

    model_config = ConfigDict(extra='ignore')

    @field_validator('datum_ingang')
    @classmethod
    def validate_datum_ingang(cls, v: Optional[str]) -> Optional[str]:
        """Validate date format and reject invalid dates."""
        if not v or v in ['0000-00-00', '']:
            return None

        try:
            datetime.strptime(v, '%Y-%m-%d')
        except (ValueError, TypeError):
            raise ValueError(f'Invalid date format for datum_ingang: {v}')

        return v

    @field_validator('ts_aangemaakt', 'ts_gewijzigd')
    @classmethod
    def validate_timestamps(cls, v: Optional[str]) -> Optional[str]:
        """Validate timestamp format."""
        if not v or v in ['0000-00-00 00:00:00', '', '0000-00-00']:
            return None

        try:
            datetime.strptime(v, '%Y-%m-%d %H:%M:%S')
        except (ValueError, TypeError):
            raise ValueError(f'Invalid timestamp format: {v}')

        return v


class AssuportalContractenAPIResponse(BaseModel):
    """Complete API response for Contracten LIST endpoint."""

    result: str = Field(..., pattern='^ok$')
    data: List[AssuportalContract] = Field(default_factory=list)
    meta: Optional[dict] = None

    model_config = ConfigDict(extra='ignore')


class AssuportalContractDetailAPIResponse(BaseModel):
    """Complete API response for Contract DETAIL endpoint."""

    result: str = Field(..., pattern='^ok$')
    data: AssuportalContract

    model_config = ConfigDict(extra='ignore')


class RelatieInput(BaseModel):
    """
    Validated input data for creating/updating a Relatie.

    This schema represents the cleaned, validated data extracted from
    Assuportal API, ready for database insertion.
    """

    relatie_id: int = Field(..., ge=1)
    hoofdnaam: str = Field(..., min_length=1)
    ts_aangemaakt: Optional[datetime] = None
    email_adressen: List[str] = Field(default_factory=list)
    source: str = Field(default='api', pattern='^(api|adviesaanvraag)$')

    model_config = ConfigDict(extra='forbid')

    @field_validator('email_adressen')
    @classmethod
    def validate_emails(cls, v: List[str]) -> List[str]:
        """Ensure all emails are valid."""
        validated = []
        for email in v:
            # Basic validation (Pydantic's EmailStr is more strict)
            if '@' in email and '.' in email:
                validated.append(email.strip().lower())
        return validated


class PersoonInput(BaseModel):
    """Validated input data for creating a Persoon."""

    api_persoon_id: int = Field(..., ge=1)
    persoon_naam: str = Field(..., min_length=1)
    persoon_email: Optional[str] = None

    model_config = ConfigDict(extra='forbid')


class ContractInput(BaseModel):
    """
    Validated input data for creating/updating a Contract.

    This schema represents the cleaned, validated data extracted from
    Assuportal API, ready for database insertion.
    """

    contract_id: int = Field(..., ge=1)
    relatie_id: int = Field(..., ge=1)
    polisnummer: str = Field(default='')
    branche: Optional[str] = None
    datum_ingang: Optional[date] = None
    ts_aangemaakt: Optional[datetime] = None
    ts_gewijzigd: Optional[datetime] = None

    model_config = ConfigDict(extra='forbid')

    @field_validator('datum_ingang')
    @classmethod
    def validate_datum_ingang_not_future(cls, v: Optional[date]) -> Optional[date]:
        """Validate date is not in far future (sanity check)."""
        if v is None:
            return v

        today = date.today()
        # Allow up to 1 year in future for contract start dates
        from datetime import timedelta
        max_future = today + timedelta(days=365)

        if v > max_future:
            raise ValueError(f'Contract start date {v} is too far in the future')

        return v
