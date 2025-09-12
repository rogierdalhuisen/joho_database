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
    list_display = ('product_module', 'level', 'premium_amount', 'currency', 'billing_cycle')
    list_filter = ('product_module__product__provider', 'product_module__product')
    search_fields = ('product_module__product__name', 'product_module__provider_specific_name', 'level__level_name')

# Simple registration for other models
admin.site.register(Providers)
admin.site.register(TargetAudiences)
admin.site.register(Products)
admin.site.register(ProductTargetAudiences)
admin.site.register(ProductModules)
admin.site.register(CoverageLevels)
admin.site.register(CoverageCategories)
admin.site.register(CoverageItems)
admin.site.register(ItemCategoryMapping)
admin.site.register(CoverageItemDetails)
admin.site.register(PremiumParameters)
admin.site.register(ParameterOptions)
# PremiumRates is now registered with the custom class above
admin.site.register(RateParameterMapping)
admin.site.register(BusinessRules)
