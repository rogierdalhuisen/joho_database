from django.contrib import admin
from .models import (
    Countries,
    Klanten,
    Aanvragen,
    Providers,
    ProviderRegions,
    ProviderRegionCountries,
    TargetAudiences,
    Products,
    ProductTargetAudiences,
    ProductModules,
    Polissen,
    BusinessRules
)


# --- Support Tables Admin ---
@admin.register(Countries)
class CountriesAdmin(admin.ModelAdmin):
    list_display = ('country_code', 'country_name')
    search_fields = ('country_name', 'country_code')


@admin.register(TargetAudiences)
class TargetAudiencesAdmin(admin.ModelAdmin):
    list_display = ('audience_id', 'audience_name')
    search_fields = ('audience_name',)


# --- Klant-gerelateerde Admin ---
@admin.register(Klanten)
class KlantenAdmin(admin.ModelAdmin):
    list_display = ('klant_id', 'emailadres', 'voorletters', 'achternaam', 'geboortedatum', 'nationaliteit_land_code')
    search_fields = ('emailadres', 'achternaam')
    list_filter = ('nationaliteit_land_code', 'aangemaakt_op')
    date_hierarchy = 'aangemaakt_op'


@admin.register(Aanvragen)
class AanvragenAdmin(admin.ModelAdmin):
    list_display = ('aanvraag_id', 'klant_id', 'bestemmings_land_code', 'vertrekdatum', 'ingediend_op')
    list_filter = ('bestemmings_land_code', 'ingediend_op')
    search_fields = ('klant_id__emailadres', 'klant_id__achternaam')
    date_hierarchy = 'ingediend_op'


@admin.register(Polissen)
class PolissenAdmin(admin.ModelAdmin):
    list_display = ('polis_id', 'polisnummer', 'klant_id', 'product_id', 'startdatum', 'totale_premie', 'status')
    list_filter = ('status', 'product_id')
    search_fields = ('polisnummer', 'klant_id__emailadres', 'klant_id__achternaam')
    date_hierarchy = 'startdatum'


# --- Provider & Product Admin ---
@admin.register(Providers)
class ProvidersAdmin(admin.ModelAdmin):
    list_display = ('provider_id', 'name', 'status', 'get_products_count', 'get_regions_count')
    list_filter = ('status',)
    search_fields = ('name',)

    def get_products_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return '0 products'
        return f'{count} products'
    get_products_count.short_description = 'Products'

    def get_regions_count(self, obj):
        count = obj.regions.count()
        if count == 0:
            return '0 regions'
        return f'{count} regions'
    get_regions_count.short_description = 'Regions'


@admin.register(ProviderRegions)
class ProviderRegionsAdmin(admin.ModelAdmin):
    list_display = ('provider_region_id', 'provider_id', 'region_name', 'get_countries_count')
    list_filter = ('provider_id',)
    search_fields = ('region_name',)

    def get_countries_count(self, obj):
        count = obj.region_countries.count()
        return f'{count} countries'
    get_countries_count.short_description = 'Countries'


@admin.register(ProviderRegionCountries)
class ProviderRegionCountriesAdmin(admin.ModelAdmin):
    list_display = ('provider_region_id', 'country_code')
    list_filter = ('provider_region_id__provider_id',)
    search_fields = ('country_code__country_name',)


# --- Product Admin with Inlines ---
class ProductModulesInline(admin.TabularInline):
    model = ProductModules
    extra = 0
    fields = ('provider_specific_name', 'is_mandatory')
    show_change_link = True


class ProductTargetAudiencesInline(admin.TabularInline):
    model = ProductTargetAudiences
    extra = 1
    verbose_name = 'Target Audience'
    verbose_name_plural = 'Target Audiences'


@admin.register(Products)
class ProductsAdmin(admin.ModelAdmin):
    list_display = (
        'product_id',
        'name',
        'provider_id',
        'policy_type',
        'get_modules_count',
        'get_target_audiences_count',
        'max_age_application',
        'max_age_coverage'
    )
    list_filter = ('provider_id', 'policy_type')
    search_fields = ('name', 'description')
    inlines = [ProductTargetAudiencesInline, ProductModulesInline]

    def get_modules_count(self, obj):
        count = obj.product_modules.count()
        if count == 0:
            return '0 modules'
        return f'{count} modules'
    get_modules_count.short_description = 'Modules'

    def get_target_audiences_count(self, obj):
        count = obj.target_audience_mappings.count()
        if count == 0:
            return 'None'
        return f'{count}'
    get_target_audiences_count.short_description = 'Target Audiences'


@admin.register(ProductModules)
class ProductModulesAdmin(admin.ModelAdmin):
    list_display = (
        'product_module_id',
        'product_id',
        'provider_specific_name',
        'is_mandatory'
    )
    list_filter = ('product_id', 'is_mandatory')
    search_fields = ('provider_specific_name',)


@admin.register(ProductTargetAudiences)
class ProductTargetAudiencesAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'audience_id')
    list_filter = ('product_id', 'audience_id')
    search_fields = ('product_id__name', 'audience_id__audience_name')


# --- Business Rules Admin ---
@admin.register(BusinessRules)
class BusinessRulesAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'scope_entity', 'scope_id', 'rule_type')
    list_filter = ('scope_entity', 'rule_type')
    search_fields = ('message',)
