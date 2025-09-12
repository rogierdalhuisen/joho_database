from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from smart_selects.db_fields import ChainedForeignKey


class Providers(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
    ]
    
    provider_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    contact_details = models.JSONField(default=dict)
    logo_url = models.CharField(max_length=500, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    class Meta:
        db_table = 'providers'
        verbose_name_plural = 'Providers'
    
    def __str__(self):
        return self.name


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
    provider = models.ForeignKey(Providers, on_delete=models.CASCADE, related_name='products')
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
        return f"{self.provider.name} - {self.name}"


class ProductTargetAudiences(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    audience = models.ForeignKey(TargetAudiences, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'product_target_audiences'
        unique_together = ('product', 'audience')
        verbose_name_plural = 'Product Target Audiences'


class ProductModules(models.Model):
    product_module_id = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='product_modules')
    is_mandatory = models.BooleanField(default=False)
    provider_specific_name = models.CharField(max_length=255, blank=True)
    premiums_available = models.BooleanField(default=True)

    class Meta:
        db_table = 'product_modules'
        verbose_name_plural = 'Product Modules'
    
    def __str__(self):
        return f"{self.product.name} - {self.provider_specific_name}"


class CoverageLevels(models.Model):
    level_id = models.AutoField(primary_key=True)
    product_module = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='coverage_levels')
    level_name = models.CharField(max_length=255)
    level_rank = models.IntegerField(validators=[MinValueValidator(1)])
    
    class Meta:
        db_table = 'coverage_levels'
        unique_together = ('product_module', 'level_rank')
        ordering = ['product_module', 'level_rank']
        verbose_name_plural = 'Coverage Levels'
    
    def __str__(self):
        return f"{self.product_module} - {self.level_name} (Rank {self.level_rank})"


class CoverageCategories(models.Model):
    category_id = models.AutoField(primary_key=True)
    parent_category = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='subcategories')
    category_name = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'coverage_categories'
        verbose_name_plural = 'Coverage Categories'
    
    def __str__(self):
        if self.parent_category:
            return f"{self.parent_category.category_name} > {self.category_name}"
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
    item = models.ForeignKey(CoverageItems, on_delete=models.CASCADE)
    category = models.ForeignKey(CoverageCategories, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'item_category_mapping'
        unique_together = ('item', 'category')
        verbose_name_plural = 'Item Category Mappings'
    
    def __str__(self):
        return f"{self.item.item_name} - {self.category.category_name}"


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
    level = models.ForeignKey(CoverageLevels, on_delete=models.CASCADE, related_name='coverage_details')
    item = models.ForeignKey(CoverageItems, on_delete=models.CASCADE, related_name='coverage_details')
    coverage_type = models.CharField(max_length=20, choices=COVERAGE_TYPE_CHOICES)
    numeric_value = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    currency = models.CharField(max_length=3, default='EUR')
    period = models.CharField(max_length=50, blank=True)
    conditions_text = models.TextField(blank=True)
    
    class Meta:
        db_table = 'coverage_item_details'
        unique_together = ('level', 'item')
        verbose_name_plural = 'Coverage Item Details'
    
    def __str__(self):
        return f"{self.level} - {self.item} ({self.coverage_type})"


class PremiumParameters(models.Model):
    parameter_id = models.AutoField(primary_key=True)
    product_module = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='premium_parameters')
    parameter_name = models.CharField(max_length=255)
    
    class Meta:
        db_table = 'premium_parameters'
        unique_together = ('product_module', 'parameter_name')
        verbose_name_plural = 'Premium Parameters'
    
    def __str__(self):
        return f"{self.product_module} - {self.parameter_name}"


class ParameterOptions(models.Model):
    option_id = models.AutoField(primary_key=True)
    parameter = models.ForeignKey(PremiumParameters, on_delete=models.CASCADE, related_name='options')
    option_value_text = models.CharField(max_length=255)
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    
    class Meta:
        db_table = 'parameter_options'
        verbose_name_plural = 'Parameter Options'
    
    def __str__(self):
        return f"{self.parameter} - {self.option_value_text}"


class PremiumRates(models.Model):
    BILLING_CYCLE_CHOICES = [('monthly', 'Monthly'), ('yearly', 'Yearly')]

    rate_id = models.AutoField(primary_key=True)
    product_module = models.ForeignKey(ProductModules, on_delete=models.CASCADE, related_name='premium_rates')
    level = ChainedForeignKey(
        CoverageLevels,
        chained_field="product_module",
        chained_model_field="product_module",
        show_all=False,
        auto_choose=True,
        sort=True,
        on_delete=models.CASCADE,
        related_name='premium_rates'
    )
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
        return f"{self.product_module} - {self.level} - €{self.premium_amount}/{self.billing_cycle}"


class RateParameterMapping(models.Model):
    rate = models.ForeignKey(PremiumRates, on_delete=models.CASCADE)
    option = models.ForeignKey(ParameterOptions, on_delete=models.CASCADE)
    
    class Meta:
        db_table = 'rate_parameter_mapping'
        unique_together = ('rate', 'option')
        verbose_name_plural = 'Rate Parameter Mappings'

    def __str__(self):
        return f"{self.rate}"


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