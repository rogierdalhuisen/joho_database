from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Countries(models.Model):
    country_code = models.CharField(max_length=3, primary_key=True)
    country_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'countries'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return f"{self.country_name} ({self.country_code})"


class Relaties(models.Model):
    SOURCE_CHOICES = [
        ('api', 'Assuportal API'),
        ('adviesaanvraag', 'Advies Aanvraag'),
    ]

    relatie_id = models.IntegerField(null=True, blank=True, unique=True, db_index=True)
    ts_aangemaakt = models.DateTimeField(null=True, blank=True)
    hoofdnaam = models.CharField(max_length=255, null=True, blank=True)
    email_adressen = models.JSONField(default=list, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='api')
    aangemaakt_op = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'relaties'
        verbose_name_plural = 'Relaties'

    def __str__(self):
        if self.hoofdnaam:
            return f"{self.hoofdnaam} (ID: {self.relatie_id or 'Nieuw'})"
        elif self.email_adressen:
            return f"Relatie - {self.email_adressen[0] if self.email_adressen else 'Geen email'}"
        return f"Relatie ID: {self.relatie_id or self.pk}"


class Personen(models.Model):
    persoon_id = models.AutoField(primary_key=True)
    relatie = models.ForeignKey(Relaties, on_delete=models.CASCADE, related_name='personen')
    api_persoon_id = models.IntegerField(null=True, blank=True)
    persoon_naam = models.CharField(max_length=255)
    persoon_email = models.EmailField(null=True, blank=True)

    class Meta:
        db_table = 'personen'
        verbose_name_plural = 'Personen'

    def __str__(self):
        return f"{self.persoon_naam} ({self.relatie.hoofdnaam})"


class AdviesAanvragen(models.Model):
    """
    Flat model voor E-grip formulier data.
    Alle velden zijn nullable omdat het formulier dynamisch is.
    """
    aanvraag_id = models.AutoField(primary_key=True)
    relatie = models.ForeignKey(Relaties, on_delete=models.CASCADE, related_name='adviesaanvragen')

    # Metadata
    external_result_id = models.CharField(max_length=100, unique=True, db_index=True, null=True, blank=True)  # TEMP nullable
    form_id = models.CharField(max_length=50, default='2')
    ingediend_op = models.DateTimeField(null=True, blank=True)  # TEMP nullable
    referral_source = models.CharField(max_length=100, null=True, blank=True)
    referral_medium = models.CharField(max_length=100, null=True, blank=True)
    referral_campaign = models.CharField(max_length=200, null=True, blank=True)
    aangemaakt_op = models.DateTimeField(default=timezone.now)  # Changed from auto_now_add

    # ============================================================================
    # PERSOONLIJKE GEGEVENS HOOFDVERZEKERDE (pos 20-120)
    # ============================================================================

    advies_voor_mezelf = models.CharField(max_length=50, null=True, blank=True)  # pos 20
    aanhef = models.CharField(max_length=20, null=True, blank=True)  # pos 50
    voorletters_roepnaam = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # pos 60
    achternaam = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # pos 70
    geboortedatum = models.DateField(null=True, blank=True)  # pos 80
    land_nationaliteit = models.CharField(max_length=100, null=True, blank=True)  # pos 90
    email = models.EmailField(db_index=True, null=True, blank=True)  # pos 100 - TEMP nullable
    telefoonnummer = models.CharField(max_length=50, null=True, blank=True)  # pos 110
    vaste_woonplaats = models.CharField(max_length=200, null=True, blank=True)  # pos 120
    geen_vaste_woonplaats = models.BooleanField(null=True, blank=True)  # pos 130

    # ============================================================================
    # MEERDERE VERZEKERDEN (pos 140-159)
    # ============================================================================

    meerdere_verzekerden = models.CharField(max_length=100, null=True, blank=True)  # pos 140
    partner_naam = models.CharField(max_length=100, null=True, blank=True)  # pos 141
    partner_geboortedatum = models.DateField(null=True, blank=True)  # pos 142
    partner_nationaliteit = models.CharField(max_length=100, null=True, blank=True)  # pos 143

    kind1_naam = models.CharField(max_length=100, null=True, blank=True)  # pos 144
    kind1_geboortedatum = models.DateField(null=True, blank=True)  # pos 145
    kind1_nationaliteit = models.CharField(max_length=100, null=True, blank=True)  # pos 146

    kind2_naam = models.CharField(max_length=100, null=True, blank=True)  # pos 147
    kind2_geboortedatum = models.DateField(null=True, blank=True)  # pos 148
    kind2_nationaliteit = models.CharField(max_length=100, null=True, blank=True)  # pos 149

    kind3_naam = models.CharField(max_length=100, null=True, blank=True)  # pos 150
    kind3_geboortedatum = models.DateField(null=True, blank=True)  # pos 151
    kind3_nationaliteit = models.CharField(max_length=100, null=True, blank=True)  # pos 152

    kind4_naam = models.CharField(max_length=100, null=True, blank=True)  # pos 153
    kind4_geboortedatum = models.DateField(null=True, blank=True)  # pos 154
    kind4_nationaliteit = models.CharField(max_length=100, null=True, blank=True)  # pos 155

    anders_personen = models.TextField(null=True, blank=True)  # pos 159

    # ============================================================================
    # SITUATIE EN PLANNEN (pos 165-248)
    # ============================================================================

    situatie_type = models.CharField(max_length=200, null=True, blank=True)  # pos 165
    bestemming_land = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # pos 170
    vertrekdatum = models.DateField(null=True, blank=True, db_index=True)  # pos 175
    uitschrijven_brp = models.CharField(max_length=50, null=True, blank=True)  # pos 220
    huidig_woonland = models.CharField(max_length=100, null=True, blank=True, db_index=True)  # pos 225
    advies_voor = models.CharField(max_length=200, null=True, blank=True)  # pos 230
    hoofdreden_verblijf = models.CharField(max_length=200, null=True, blank=True)  # pos 240
    toelichting_hoofdreden = models.TextField(null=True, blank=True)  # pos 245
    verwachte_duur_verblijf = models.CharField(max_length=100, null=True, blank=True)  # pos 247
    toelichting_duur = models.TextField(null=True, blank=True)  # pos 248

    # ============================================================================
    # WERK EN INKOMEN (pos 250-270)
    # ============================================================================

    werk_omschrijving = models.TextField(null=True, blank=True)  # pos 250
    plannen_omschrijving = models.TextField(null=True, blank=True)  # pos 260
    salaris_uit_nederland = models.CharField(max_length=50, null=True, blank=True)  # pos 270

    # ============================================================================
    # ARBEIDSONGESCHIKTHEIDSVERZEKERING (pos 280-416)
    # ============================================================================

    interesse_aov = models.CharField(max_length=50, null=True, blank=True)  # pos 280
    loondienst_of_zelfstandig = models.CharField(max_length=50, null=True, blank=True)  # pos 290
    eigen_onderneming_3jaar = models.CharField(max_length=50, null=True, blank=True)  # pos 300
    bruto_jaarinkomen = models.CharField(max_length=100, null=True, blank=True)  # pos 310
    aov_geen_offerte_reden = models.TextField(null=True, blank=True)  # pos 320
    loon_doorbetaald_bij_ziekte = models.CharField(max_length=200, null=True, blank=True)  # pos 330
    toelichting_uitkering = models.TextField(null=True, blank=True)  # pos 340
    bruto_salaris_inkomen = models.CharField(max_length=100, null=True, blank=True)  # pos 350
    salaris_per_maand_jaar = models.CharField(max_length=50, null=True, blank=True)  # pos 360
    bouwplaats_of_offshore = models.CharField(max_length=50, null=True, blank=True)  # pos 370
    bouwplaats_hoe_vaak = models.CharField(max_length=100, null=True, blank=True)  # pos 380
    gevaarlijke_stoffen = models.CharField(max_length=50, null=True, blank=True)  # pos 390
    toelichting_gevaarlijke_stoffen = models.TextField(null=True, blank=True)  # pos 400
    interesse_internationale_aov = models.CharField(max_length=50, null=True, blank=True)  # pos 411
    geen_interesse_aov_reden = models.TextField(null=True, blank=True)  # pos 412
    functieomschrijving = models.CharField(max_length=200, null=True, blank=True)  # pos 413
    type_werkzaamheden = models.CharField(max_length=100, null=True, blank=True)  # pos 414
    verwacht_inkomen = models.CharField(max_length=100, null=True, blank=True)  # pos 415
    inkomen_toelichting = models.TextField(null=True, blank=True)  # pos 416

    # ============================================================================
    # ZIEKTEKOSTENVERZEKERING (pos 419-560)
    # ============================================================================

    interesse_zkv = models.CharField(max_length=50, null=True, blank=True, db_index=True)  # pos 419
    zkv_geen_interesse_reden = models.TextField(null=True, blank=True)  # pos 420
    zkv_dekkingsvariant = models.CharField(max_length=50, null=True, blank=True)  # pos 430
    zkv_eigen_risico_voorkeur = models.CharField(max_length=50, null=True, blank=True)  # pos 440
    zkv_eigen_risico_bedrag = models.CharField(max_length=50, null=True, blank=True)  # pos 450
    zkv_periode = models.CharField(max_length=100, null=True, blank=True)  # pos 460
    zkv_periode_omschrijving_motivatie = models.TextField(null=True, blank=True)  # pos 470
    zkv_periode_omschrijving = models.TextField(null=True, blank=True)  # pos 480
    huidige_verzekeraar = models.CharField(max_length=100, null=True, blank=True)  # pos 490
    voorkeur_verzekeraar = models.CharField(max_length=100, null=True, blank=True)  # pos 500
    medische_bijzonderheden = models.CharField(max_length=50, null=True, blank=True)  # pos 510
    medische_bijzonderheden_toelichting = models.TextField(null=True, blank=True)  # pos 520
    specifieke_wensen_zkv = models.CharField(max_length=50, null=True, blank=True)  # pos 530
    wensen_toelichting = models.TextField(null=True, blank=True)  # pos 540
    dekking_zwangerschap = models.CharField(max_length=50, null=True, blank=True)  # pos 550
    zwangerschap_toelichting = models.TextField(null=True, blank=True)  # pos 560

    # ============================================================================
    # AANVULLENDE VERZEKERINGEN (pos 565-569)
    # ============================================================================

    andere_verzekeringen_interesse = models.TextField(null=True, blank=True)  # pos 565 - comma separated
    overlijdensrisico_bedrag = models.CharField(max_length=100, null=True, blank=True)  # pos 566
    overlijdensrisico_bedrag_anders = models.CharField(max_length=100, null=True, blank=True)  # pos 567
    overlijdensrisico_bestemming = models.TextField(null=True, blank=True)  # pos 568
    overlijdensrisico_bestemming_anders = models.TextField(null=True, blank=True)  # pos 569

    # ============================================================================
    # SPORTEN EN ACTIVITEITEN (pos 570-600)
    # ============================================================================

    sporten_activiteiten = models.TextField(null=True, blank=True)  # pos 580
    sport_semiprofessioneel = models.CharField(max_length=50, null=True, blank=True)  # pos 590
    sport_professioneel_omschrijving = models.TextField(null=True, blank=True)  # pos 600

    # ============================================================================
    # HUIS IN NEDERLAND (pos 650-710)
    # ============================================================================

    huis_in_nederland = models.CharField(max_length=50, null=True, blank=True)  # pos 660
    huis_type = models.CharField(max_length=50, null=True, blank=True)  # pos 670
    woning_verhuurd = models.CharField(max_length=50, null=True, blank=True)  # pos 680
    woning_eigen_gebruik = models.CharField(max_length=50, null=True, blank=True)  # pos 690
    woning_verblijf_frequentie = models.CharField(max_length=200, null=True, blank=True)  # pos 700
    woning_opmerkingen = models.TextField(null=True, blank=True)  # pos 710

    # ============================================================================
    # MARKETING EN CONTACT (pos 730-830)
    # ============================================================================

    hoe_gevonden = models.CharField(max_length=100, null=True, blank=True)  # pos 740
    welke_website = models.CharField(max_length=200, null=True, blank=True)  # pos 750
    naam_werkgever = models.CharField(max_length=200, null=True, blank=True)  # pos 760
    hoe_gevonden_overig = models.TextField(null=True, blank=True)  # pos 770
    eerder_contact_joho = models.CharField(max_length=50, null=True, blank=True)  # pos 780
    eerder_contact_keuze = models.CharField(max_length=100, null=True, blank=True)  # pos 790
    naam_contactpersoon = models.CharField(max_length=200, null=True, blank=True)  # pos 800
    eerder_contact_anders = models.TextField(null=True, blank=True)  # pos 810
    advies_vorm = models.CharField(max_length=50, null=True, blank=True)  # pos 820

    # ============================================================================
    # BACKUP: Volledige raw data
    # ============================================================================

    raw_form_data = models.JSONField(null=True, blank=True)  # Volledige API response voor audit

    class Meta:
        db_table = 'adviesaanvragen'
        verbose_name_plural = 'Advies Aanvragen'
        indexes = [
            models.Index(fields=['email', 'ingediend_op']),
            models.Index(fields=['bestemming_land', 'vertrekdatum']),
            models.Index(fields=['interesse_zkv', 'ingediend_op']),
        ]

    def __str__(self):
        naam = f"{self.voorletters_roepnaam or ''} {self.achternaam or ''}".strip() or "Onbekend"
        bestemming = self.bestemming_land or self.huidig_woonland or "?"
        return f"Aanvraag {self.aanvraag_id} - {naam} naar {bestemming}"


class Contracten(models.Model):
    contract_id = models.IntegerField(primary_key=True)
    polisnummer = models.CharField(max_length=255, blank=True)
    branche = models.CharField(max_length=255, null=True, blank=True)
    relatie = models.ForeignKey(Relaties, on_delete=models.PROTECT, related_name='contracten')
    datum_ingang = models.DateField(null=True, blank=True)
    ts_aangemaakt = models.DateTimeField(null=True, blank=True)
    ts_gewijzigd = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'contracten'
        verbose_name_plural = 'Contracten'

    def __str__(self):
        return f"Contract {self.polisnummer} - {self.relatie}"


class Providers(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    provider_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'providers'
        verbose_name_plural = 'Providers'

    def __str__(self):
        return self.name


class ProviderRegions(models.Model):
    provider_region_id = models.AutoField(primary_key=True)
    provider_id = models.ForeignKey(Providers, on_delete=models.CASCADE, related_name='regions')
    region_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'provider_regions'
        verbose_name_plural = 'Provider Regions'

    def __str__(self):
        return f"{self.provider_id.name} - {self.region_name}"


class ProviderRegionCountries(models.Model):
    provider_region_id = models.ForeignKey(ProviderRegions, on_delete=models.CASCADE, related_name='region_countries')
    country_code = models.ForeignKey(Countries, on_delete=models.CASCADE, related_name='provider_regions')

    class Meta:
        db_table = 'provider_region_countries'
        unique_together = ('provider_region_id', 'country_code')
        verbose_name_plural = 'Provider Region Countries'


class TargetAudiences(models.Model):
    audience_id = models.AutoField(primary_key=True)
    audience_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'target_audiences'
        verbose_name_plural = 'Target Audiences'

    def __str__(self):
        return self.audience_name


class Products(models.Model):
    POLICY_TYPE_CHOICES = [
        ('flexible', 'Flexible'),
        ('individual', 'Individual'),
        ('family', 'Family'),
        ('group', 'Group'),
        ('corporate', 'Corporate'),
    ]

    product_id = models.AutoField(primary_key=True)
    provider_id = models.ForeignKey(Providers, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    max_age_application = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    max_age_coverage = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    target_audiences = models.ManyToManyField(
        TargetAudiences,
        through='ProductTargetAudiences',
        related_name='products'
    )

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'Products'

    def __str__(self):
        return f"{self.provider_id.name} - {self.name}"


class ProductTargetAudiences(models.Model):
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='target_audience_mappings')
    audience_id = models.ForeignKey(TargetAudiences, on_delete=models.CASCADE, related_name='product_target_mappings')

    class Meta:
        db_table = 'product_target_audiences'
        unique_together = ('product_id', 'audience_id')
        verbose_name_plural = 'Product Target Audiences'


class ProductModules(models.Model):
    product_module_id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='product_modules')
    is_mandatory = models.BooleanField(default=False)
    provider_specific_name = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'product_modules'
        verbose_name_plural = 'Product Modules'

    def __str__(self):
        product_name = self.product_id.name
        module_display = self.provider_specific_name or f"Module ID: {self.product_module_id}"
        return f"{product_name} - {module_display}"


class BusinessRules(models.Model):
    SCOPE_ENTITY_CHOICES = [
        ('provider', 'Provider'),
        ('product', 'Product'),
        ('module', 'Module'),
        ('coverage', 'Coverage'),
        ('parameter', 'Parameter'),
    ]

    RULE_TYPE_CHOICES = [
        ('eligibility', 'Eligibility Rule'),
        ('validation', 'Validation Rule'),
        ('calculation', 'Calculation Rule'),
        ('exclusion', 'Exclusion Rule'),
        ('dependency', 'Dependency Rule'),
    ]

    rule_id = models.AutoField(primary_key=True)
    scope_entity = models.CharField(max_length=20, choices=SCOPE_ENTITY_CHOICES)
    scope_id = models.IntegerField()
    rule_type = models.CharField(max_length=20, choices=RULE_TYPE_CHOICES)
    condition_json = models.JSONField()
    message = models.TextField()

    class Meta:
        db_table = 'business_rules'
        verbose_name_plural = 'Business Rules'

    def __str__(self):
        return f"{self.scope_entity}:{self.scope_id} - {self.rule_type}"
