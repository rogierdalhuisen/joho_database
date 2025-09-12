from django.contrib import admin
from .models import (
    Providers,
    TargetAudiences,
    Products,
    ProductTargetAudiences,
    ProductModules,
    CoverageLevels,
    CoverageCategories,
    CoverageItems,
    ItemCategoryMapping,
    CoverageItemDetails,
    PremiumParameters,
    ParameterOptions,
    PremiumRates,
    RateParameterMapping,
    BusinessRules
)
@admin.register(PremiumRates)
class PremiumRatesAdmin(admin.ModelAdmin):
    list_display = ('product_module', 'level', 'premium_amount')
    list_filter = ('product_module__product',)

@admin.register(CoverageLevels)
class CoverageLevelsAdmin(admin.ModelAdmin):
    list_display = ('product_module', 'level_name')
    list_filter = ('product_module__product',)

@admin.register(PremiumParameters)
class PremiumParametersAdmin(admin.ModelAdmin):
    list_display = ('product_module', 'parameter_name')
    list_filter = ('product_module__product',)

@admin.register(ParameterOptions)
class ParameterOptionsAdmin(admin.ModelAdmin):
    list_display = ('parameter', 'option_value_text')
    list_filter = ('parameter__product_module__product',)

@admin.register(ProductModules)
class ProductModulesAdmin(admin.ModelAdmin):
    list_display = ('product', 'provider_specific_name',
                    'is_mandatory')
    list_filter = ('product',)

@admin.register(CoverageItemDetails)
class CoverageItemDetailsAdmin(admin.ModelAdmin):
    list_display = ('level', 'item', 'coverage_type')
    list_filter = ('level__product_module__product',)

@admin.register(RateParameterMapping)
class RateParameterMappingAdmin(admin.ModelAdmin):
    list_display = ('rate', 'option')
    list_filter = ('rate__product_module__product',)

# Simple registration for other models
admin.site.register(Providers)
admin.site.register(TargetAudiences)
admin.site.register(Products)
admin.site.register(ProductTargetAudiences)

admin.site.register(CoverageCategories)
admin.site.register(CoverageItems)
admin.site.register(ItemCategoryMapping)
# admin.site.register(ParameterOptions)
# PremiumRates is now registered with the custom class above
admin.site.register(BusinessRules)
