from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


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
    aangemaakt_op = models.DateTimeField(auto_now_add=True)

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
    aanvraag_id = models.AutoField(primary_key=True)
    relatie = models.ForeignKey(Relaties, on_delete=models.CASCADE, related_name='adviesaanvragen')
    email_identifier = models.EmailField()
    bestemmings_land_code = models.ForeignKey(Countries, on_delete=models.PROTECT, related_name='aanvragen_bestemming')
    vertrekdatum = models.DateField()
    ingediend_op = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'adviesaanvragen'
        verbose_name_plural = 'Advies Aanvragen'

    def __str__(self):
        return f"Aanvraag {self.aanvraag_id} - {self.relatie} naar {self.bestemmings_land_code}"


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


class Polissen(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('pending', 'Pending'),
        ('cancelled', 'Cancelled'),
        ('expired', 'Expired'),
    ]

    polis_id = models.AutoField(primary_key=True)
    polisnummer = models.CharField(max_length=255, unique=True)
    relatie = models.ForeignKey(Relaties, on_delete=models.CASCADE, related_name='polissen')
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='polissen')
    startdatum = models.DateField()
    totale_premie = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'polissen'
        verbose_name_plural = 'Polissen'

    def __str__(self):
        return f"Polis {self.polisnummer} - {self.relatie}"


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
