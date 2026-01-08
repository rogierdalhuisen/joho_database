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


class Klanten(models.Model):
    klant_id = models.AutoField(primary_key=True)
    emailadres = models.EmailField(unique=True)
    voorletters = models.CharField(max_length=10)
    achternaam = models.CharField(max_length=255)
    geboortedatum = models.DateField()
    nationaliteit_land_code = models.ForeignKey(Countries, on_delete=models.PROTECT, related_name='nationals')
    aangemaakt_op = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'klanten'
        verbose_name_plural = 'Klanten'

    def __str__(self):
        return f"{self.voorletters} {self.achternaam} ({self.emailadres})"


class Aanvragen(models.Model):
    aanvraag_id = models.AutoField(primary_key=True)
    klant_id = models.ForeignKey(Klanten, on_delete=models.CASCADE, related_name='aanvragen')
    bestemmings_land_code = models.ForeignKey(Countries, on_delete=models.PROTECT, related_name='aanvragen_bestemming')
    vertrekdatum = models.DateField()
    ingediend_op = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'aanvragen'
        verbose_name_plural = 'Aanvragen'

    def __str__(self):
        return f"Aanvraag {self.aanvraag_id} - {self.klant_id} naar {self.bestemmings_land_code}"


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
    klant_id = models.ForeignKey(Klanten, on_delete=models.CASCADE, related_name='polissen')
    product_id = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='polissen')
    startdatum = models.DateField()
    totale_premie = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'polissen'
        verbose_name_plural = 'Polissen'

    def __str__(self):
        return f"Polis {self.polisnummer} - {self.klant_id}"


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
