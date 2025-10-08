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
    emailadres = models.EmailField(unique=True)
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    class Meta:
        db_table = 'verzekeraars'
        verbose_name_plural = 'Verzekeraars'

    def __str__(self):
        return self.naam


class VerzekeraarRegio(models.Model):
    verzekeraar_regio_id = models.AutoField(primary_key=True)
    verzekeraar_id = models.ForeignKey(Verzekeraars, on_delete=models.CASCADE, related_name='regios')
    regio_naam = models.CharField(max_length=255)

    class Meta:
        db_table = 'verzekeraar_regio'
        verbose_name_plural = 'Verzekeraar Regio'

    def __str__(self):
        return f"{self.verzekeraar_id.naam} - {self.regio_naam}"


class VerzekeraarRegioLanden(models.Model):
    verzekeraar_regio_id = models.ForeignKey(VerzekeraarRegio, on_delete=models.CASCADE, related_name='regio_landen')
    land_code = models.ForeignKey(Landen, on_delete=models.CASCADE, related_name='regio_landen')

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
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    max_leeftijd_aanvraag = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    max_leeftijd_dekking = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(120)])
    target_doelgroepen = models.ManyToManyField(
        Doelgroepen,
        through='ProductTargetDoelgroepen',
        related_name='products'
    )

    class Meta:
        db_table = 'products'
        verbose_name_plural = 'Producten'

    def __str__(self):
        return f"{self.verzekeraar_id.naam} - {self.naam}"


class ProductTargetDoelgroepen(models.Model):
    product_id = models.ForeignKey(Producten, on_delete=models.CASCADE, related_name='target_doelgroep_mappings')
    doelgroep_id = models.ForeignKey(Doelgroepen, on_delete=models.CASCADE, related_name='product_target_mappings')

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


class DekkingsNiveaus(models.Model):
    niveau_id = models.AutoField(primary_key=True)
    niveau_name = models.CharField(max_length=255)
    niveau_rank = models.IntegerField(validators=[MinValueValidator(1)])

    class Meta:
        db_table = 'dekkings_niveaus'
        ordering = ['niveau_rank']
        verbose_name_plural = 'Dekkings Niveaus'

    def __str__(self):
        return f"{self.niveau_name} (Rank {self.niveau_rank})"


class DekkingsCategorien(models.Model):
    categorie_id = models.AutoField(primary_key=True)
    parent_categorie_id = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    categorie_naam = models.CharField(max_length=255)

    class Meta:
        db_table = 'dekkings_categorien'
        verbose_name_plural = 'Dekkings Categorien'

    def __str__(self):
        if self.parent_categorie_id:
            return f"{self.parent_categorie_id.categorie_naam} > {self.categorie_naam}"
        return self.categorie_naam


class DekkingsItems(models.Model):
    item_id = models.AutoField(primary_key=True)
    item_naam = models.CharField(max_length=255)
    categorien = models.ManyToManyField(
        DekkingsCategorien,
        through='ItemCategorieMapping',
        related_name='dekkings_items'
    )

    class Meta:
        db_table = 'dekkings_items'
        verbose_name_plural = 'Dekkings Items'

    def __str__(self):
        return self.item_naam


class ItemCategorieMapping(models.Model):
    item_id = models.ForeignKey(DekkingsItems, on_delete=models.CASCADE, related_name='item_categorie_mappings')
    categorie_id = models.ForeignKey(DekkingsCategorien, on_delete=models.CASCADE, related_name='item_categorie_mappings')

    class Meta:
        db_table = 'item_category_mapping'
        unique_together = ('item_id', 'categorie_id')
        verbose_name_plural = 'Item Category Mappings'

    def __str__(self):
        return f"{self.item_id.item_naam} - {self.categorie_id.categorie_naam}"


class DekkingsItemDetails(models.Model):
    COVERAGE_TYPE_CHOICES = [
        ('amount', 'Fixed Amount'),
        ('percentage', 'Percentage'),
        ('limit', 'Coverage Limit'),
        ('deductible', 'Deductible'),
        ('excluded', 'Excluded'),
        ('included', 'Included'),
    ]

    detail_id = models.AutoField(primary_key=True)
    niveau_id = models.ForeignKey(DekkingsNiveaus, on_delete=models.CASCADE, related_name='dekking_details')
    item_id = models.ForeignKey(DekkingsItems, on_delete=models.CASCADE, related_name='dekking_details')
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='dekking_details')
    dekkings_type = models.CharField(max_length=20, choices=COVERAGE_TYPE_CHOICES)
    numerieke_waarde = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    valuta = models.CharField(max_length=3, default='EUR')
    periode = models.CharField(max_length=50, blank=True)
    voorwaarden_tekst = models.TextField(blank=True)

    class Meta:
        db_table = 'dekkings_item_details'
        unique_together = ('niveau_id', 'item_id', 'product_module_id')
        verbose_name_plural = 'Dekkings Item Details'

    def __str__(self):
        return f"{self.niveau_id} - {self.item_id} ({self.dekkings_type})"


class PremieParameters(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='premie_parameters')
    parameter_naam = models.CharField(max_length=255)

    class Meta:
        db_table = 'premie_parameters'
        unique_together = ('product_module_id', 'parameter_naam')
        verbose_name_plural = 'Premie Parameters'

    def __str__(self):
        return f"{self.product_module_id} - {self.parameter_naam}"


class ParameterOpties(models.Model):
    optie_id = models.AutoField(primary_key=True)
    parameter_id = models.ForeignKey(PremieParameters, on_delete=models.CASCADE, related_name='opties')
    optie_waarde_tekst = models.CharField(max_length=255)
    min_waarde = models.IntegerField(null=True, blank=True)
    max_waarde = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = 'parameter_opties'
        verbose_name_plural = 'Parameter Opties'

    def __str__(self):
        return f"{self.parameter_id} - {self.optie_waarde_tekst}"


class Premies(models.Model):
    BILLING_CYCLE_CHOICES = [('monthly', 'Monthly'), ('yearly', 'Yearly')]

    premie_id = models.AutoField(primary_key=True)
    product_module_id = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='premies')
    level_id = models.ForeignKey(DekkingsNiveaus, on_delete=models.CASCADE, related_name='premies')
    premie = models.DecimalField(max_digits=10, decimal_places=2)
    valuta = models.CharField(max_length=3, default='EUR')
    termijn = models.CharField(max_length=20, choices=BILLING_CYCLE_CHOICES)
    parameter_opties = models.ManyToManyField(
        ParameterOpties,
        through='PremieParameterMapping',
        related_name='premies'
    )

    class Meta:
        db_table = 'premies'
        verbose_name_plural = 'Premies'

    def __str__(self):
        return f"{self.level_id} - €{self.premie}/{self.termijn}"


class PremieParameterMapping(models.Model):
    premie_id = models.ForeignKey(Premies, on_delete=models.CASCADE, related_name='parameter_mappings')
    optie_id = models.ForeignKey(ParameterOpties, on_delete=models.CASCADE, related_name='premie_mappings')

    class Meta:
        db_table = 'premie_parameter_mapping'
        unique_together = ('premie_id', 'optie_id')
        verbose_name_plural = 'Premie Parameter Mappings'

    def __str__(self):
        return f"{self.premie_id}"


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
    level_id = models.ForeignKey(DekkingsNiveaus, on_delete=models.CASCADE, related_name='polis_modules')

    class Meta:
        db_table = 'polis_modules'
        verbose_name_plural = 'Polis Modules'

    def __str__(self):
        return f"{self.polis_id} - {self.product_module_id}"


class PolisOpties(models.Model):
    polis_optie_id = models.AutoField(primary_key=True)
    polis_id = models.ForeignKey(Polissen, on_delete=models.CASCADE, related_name='polis_opties')
    option_id = models.ForeignKey(ParameterOpties, on_delete=models.CASCADE, related_name='polis_opties')

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