from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.postgres.fields import ArrayField


class Landen(models.Model):
    land_code = models.CharField(max_length=3, primary_key=True)
    land_naam = models.CharField(max_length=255)

    class Meta:
        db_table = 'landen'
        verbose_name_plural = 'Landen'

    def __str__(self):
        return f"{self.land_naam} ({self.land_code})"


class Klanten(models.Model):
    klant_id = models.AutoField(primary_key=True)
    email_adres = models.EmailField(unique=True)
    voorletters = models.CharField(max_length=10)
    achternaam = models.CharField(max_length=255)
    geboortedatum = models.DateField()
    nationaliteit_land_code = models.ForeignKey(Landen, on_delete=models.PROTECT, related_name='nationals')
    aangemaakt_op = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'klanten'
        verbose_name_plural = 'Klanten'

    def __str__(self):
        return f"{self.voorletters} {self.achternaam} ({self.emailadres})"


class Aanvragen(models.Model):
    aanvraag_id = models.AutoField(primary_key=True)
    klant_id = models.ForeignKey(Klanten, on_delete=models.CASCADE, related_name='aanvragen')
    bestemmings_land_code = models.ForeignKey(Landen, on_delete=models.PROTECT, related_name='aanvragen_bestemming')
    vertrekdatum = models.DateField()
    ingediend_op = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'aanvragen'
        verbose_name_plural = 'Aanvragen'

    def __str__(self):
        return f"Aanvraag {self.aanvraag_id} - {self.klant_id} naar {self.bestemmings_land_code}"


class Verzekeraars(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]

    verzekeraar_id = models.AutoField(primary_key=True)
    naam = models.CharField(max_length=255)
    contact_details = models.JSONField(default=dict)
    logo_url = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'verzekeraars'
        verbose_name_plural = 'Verzekeraars'

    def __str__(self):
        return self.naam


class VerzekeraarRegio(models.Model):
    verzekeraar_regio_id = models.AutoField(primary_key=True)
    verzekeraar_id = models.ForeignKey(Verzekeraars, on_delete=models.CASCADE, related_name='regions')
    regio_naam = models.CharField(max_length=255)

    class Meta:
        db_table = 'verzekeraar_regio'
        verbose_name_plural = 'Verzekeraar Regio'

    def __str__(self):
        return f"{self.provider_id.name} - {self.region_name}"


class VerzekeraarRegioLanden(models.Model):
    verzekeraar_regio_id = models.ForeignKey(VerzekeraarRegio, on_delete=models.CASCADE)
    land_code = models.ForeignKey(Landen, on_delete=models.CASCADE)

    class Meta:
        db_table = 'verzekeraar_regio_landen'
        unique_together = ('verzekeraar_regio_id', 'land_code')
        verbose_name_plural = 'Verzekeraar Regio Landen'


class Doelgroepen(models.Model):
    doelgroep_id = models.AutoField(primary_key=True)
    doelgroep_naam = models.CharField(max_length=255)

    class Meta:
        db_table = 'doelgroepen'
        verbose_name_plural = 'Doelgroepen'

    def __str__(self):
        return self.doelgroep_naam


class Producten(models.Model):
    POLICY_TYPE_CHOICES = [
        ('flexible', 'Flexible'),
        ('individual', 'Individual'),
        ('family', 'Family'),
        ('group', 'Group'),
        ('corporate', 'Corporate'),
    ]

    product_id = models.AutoField(primary_key=True)
    verzekeraar_id = models.ForeignKey(Verzekeraars, on_delete=models.CASCADE, related_name='products')
    naam = models.CharField(max_length=255)
    beschrijving = models.TextField(blank=True)
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    max_leeftijd_aanvraag = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    max_leeftijd_dekking = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    target_doelgroepen = models.ManyToManyField(
        Doelgroepen,
        through='ProductTargetAudiess ProductTargetDoelgroepen',
        related_name='products'
    )

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'Producten'

    def __str__(self):
        return f"{self.provider_id.name} - {self.name}"


class ProductTargetDoelgroepen(models.Model):
    product_id = models.ForeignKey(Producten, on_delete=models.CASCADE)
    doelgroep_id = models.ForeignKey(Doelgroepen, on_delete=models.CASCADE)

    class Meta:
        db_table = 'product_target_doelgroepen'
        unique_together = ('product_id', 'doelgroep_id')
        verbose_name_plural = 'Product Target Doelgroepen'


class ProductModules(models.Model):
    product_module_id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Producten, on_delete=models.CASCADE, related_name='product_modules')
    is_verplicht = models.BooleanField(default=False)
    module_naam = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'product_modules'
        verbose_name_plural = 'Product Modules'

    def __str__(self):
        return self.module_naam or f"Module ID: {self.product_module_id}"


class DocumentChunk(models.Model):
    chunk_id = models.AutoField(primary_key=True)
    product_id = models.ForeignKey(Producten, on_delete=models.CASCADE, related_name='document_chunks')
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='document_chunks', null=True, blank=True)
    content = models.TextField()
    embedding = ArrayField(models.FloatField(), size=None, null=True, blank=True)
    metadata = models.JSONField(default=dict)

    class Meta:
        db_table = 'document_chunk'
        verbose_name_plural = 'Document Chunks'

    def __str__(self):
        return f"Chunk {self.chunk_id} - {self.product_id}"


class CoverageLevels(models.Model):
    level_id = models.AutoField(primary_key=True)
    level_name = models.CharField(max_length=255)
    level_rank = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'coverage_levels'
        ordering = ['level_rank']
        verbose_name_plural = 'Coverage Levels'

    def __str__(self):
        return f"{self.level_name} (Rank {self.level_rank})"


class CoverageCategories(models.Model):
    category_id = models.AutoField(primary_key=True)
    parent_category_id = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    category_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'coverage_categories'
        verbose_name_plural = 'Coverage Categories'

    def __str__(self):
        if self.parent_category_id:
            return f"{self.parent_category_id.category_name} > {self.category_name}"
        return self.category_name


class CoverageItems(models.Model):
    item_id = models.AutoField(primary_key=True)
    item_name = models.CharField(max_length=255)
    categories = models.ManyToManyField(
        CoverageCategories,
        through='ItemCategoryMapping',
        related_name='coverage_items'
    )

    class Meta:
        db_table = 'coverage_items'
        verbose_name_plural = 'Coverage Items'

    def __str__(self):
        return self.item_name


class ItemCategoryMapping(models.Model):
    item_id = models.ForeignKey(CoverageItems, on_delete=models.CASCADE)
    category_id = models.ForeignKey(CoverageCategories, on_delete=models.CASCADE)

    class Meta:
        db_table = 'item_category_mapping'
        unique_together = ('item_id', 'category_id')
        verbose_name_plural = 'Item Category Mappings'

    def __str__(self):
        return f"{self.item_id.item_name} - {self.category_id.category_name}"


class CoverageItemDetails(models.Model):
    COVERAGE_TYPE_CHOICES = [
        ('amount', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ('limit', 'Coverage Limit'),
        ('deductible', 'Deductible'),
        ('excluded', 'Excluded'),
        ('included', 'Included'),
    ]

    detail_id = models.AutoField(primary_key=True)
    level_id = models.ForeignKey(CoverageLevels, on_delete=models.CASCADE, related_name='coverage_details')
    item_id = models.ForeignKey(CoverageItems, on_delete=models.CASCADE, related_name='coverage_details')
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='coverage_details')
    coverage_type = models.CharField(max_length=20, choices=COVERAGE_TYPE_CHOICES)
    numeric_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='EUR')
    period = models.CharField(max_length=50, blank=True)
    conditions_text = models.TextField(blank=True)

    class Meta:
        db_table = 'coverage_item_details'
        unique_together = ('level_id', 'item_id', 'product_module_id')
        verbose_name_plural = 'Coverage Item Details'

    def __str__(self):
        return f"{self.level_id} - {self.item_id} ({self.coverage_type})"


class PremiumParameters(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='premium_parameters')
    parameter_name = models.CharField(max_length=255)

    class Meta:
        db_table = 'premium_parameters'
        unique_together = ('product_module_id', 'parameter_name')
        verbose_name_plural = 'Premium Parameters'

    def __str__(self):
        return f"{self.product_module_id} - {self.parameter_name}"


class ParameterOptions(models.Model):
    option_id = models.AutoField(primary_key=True)
    parameter_id = models.ForeignKey(PremiumParameters, on_delete=models.CASCADE, related_name='options')
    option_value_text = models.CharField(max_length=255)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'parameter_options'
        verbose_name_plural = 'Parameter Options'

    def __str__(self):
        return f"{self.parameter_id} - {self.option_value_text}"


class PremiumRates(models.Model):
    BILLING_CYCLE_CHOICES = [('monthly', 'Monthly'), ('yearly', 'Yearly')]

    rate_id = models.AutoField(primary_key=True)
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='premium_rates')
    level_id = models.ForeignKey(CoverageLevels, on_delete=models.CASCADE, related_name='premium_rates')
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='EUR')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    parameter_options = models.ManyToManyField(
        ParameterOptions,
        through='RateParameterMapping',
        related_name='premium_rates'
    )

    class Meta:
        db_table = 'premium_rates'
        verbose_name_plural = 'Premium Rates'

    def __str__(self):
        return f"{self.level_id} - €{self.premium_amount}/{self.billing_cycle}"


class RateParameterMapping(models.Model):
    rate_id = models.ForeignKey(PremiumRates, on_delete=models.CASCADE)
    option_id = models.ForeignKey(ParameterOptions, on_delete=models.CASCADE)

    class Meta:
        db_table = 'rate_parameter_mapping'
        unique_together = ('rate_id', 'option_id')
        verbose_name_plural = 'Rate Parameter Mappings'

    def __str__(self):
        return f"{self.rate_id}"


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
    product_id = models.ForeignKey(Producten, on_delete=models.CASCADE, related_name='polissen')
    startdatum = models.DateField()
    totale_premie = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    class Meta:
        db_table = 'polissen'
        verbose_name_plural = 'Polissen'

    def __str__(self):
        return f"Polis {self.polisnummer} - {self.klant_id}"


class PolisModules(models.Model):
    polis_module_id = models.AutoField(primary_key=True)
    polis_id = models.ForeignKey(Polissen, on_delete=models.CASCADE, related_name='polis_modules')
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='polis_modules')
    level_id = models.ForeignKey(CoverageLevels, on_delete=models.CASCADE, related_name='polis_modules')

    class Meta:
        db_table = 'polis_modules'
        verbose_name_plural = 'Polis Modules'

    def __str__(self):
        return f"{self.polis_id} - {self.product_module_id}"


class PolisOpties(models.Model):
    polis_optie_id = models.AutoField(primary_key=True)
    polis_id = models.ForeignKey(Polissen, on_delete=models.CASCADE, related_name='polis_opties')
    option_id = models.ForeignKey(ParameterOptions, on_delete=models.CASCADE, related_name='polis_opties')

    class Meta:
        db_table = 'polis_opties'
        verbose_name_plural = 'Polis Opties'

    def __str__(self):
        return f"{self.polis_id} - {self.option_id}"


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