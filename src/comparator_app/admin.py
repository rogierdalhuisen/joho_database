from django.contrib import admin
from .models import (
    Providers,
    TargetAudiences,
    Products,
    ProductTargetAudiences,
    Modules,
    ProductModules,
    CoverageLevels,
    CoverageCategories,
    CoverageItems,
    CoverageItemDetails,
    PremiumParameters,
    ParameterOptions,
    PremiumRates,
    RateParameterMapping,
    BusinessRules
)

# Simple registration for most models
admin.site.register(Providers)
admin.site.register(TargetAudiences)
admin.site.register(Products)
admin.site.register(ProductTargetAudiences)
admin.site.register(Modules)
admin.site.register(ProductModules)
admin.site.register(CoverageLevels)
admin.site.register(CoverageCategories)
admin.site.register(CoverageItems)
admin.site.register(CoverageItemDetails)
admin.site.register(PremiumParameters)
admin.site.register(ParameterOptions)
admin.site.register(PremiumRates)
admin.site.register(RateParameterMapping)
admin.site.register(BusinessRules)
