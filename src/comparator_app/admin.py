from django.contrib import admin
from .models import (
    Countries,
    Relaties,
    Personen,
    AdviesAanvragen,
    Contracten,
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


# --- Relatie-gerelateerde Admin ---
class PersonenInline(admin.TabularInline):
    model = Personen
    extra = 0
    fields = ('api_persoon_id', 'persoon_naam', 'persoon_email')
    show_change_link = True


@admin.register(Relaties)
class RelatiesAdmin(admin.ModelAdmin):
    list_display = ('relatie_id', 'hoofdnaam', 'get_email_display', 'source', 'aangemaakt_op')
    search_fields = ('hoofdnaam', 'relatie_id')
    list_filter = ('source', 'aangemaakt_op')
    date_hierarchy = 'aangemaakt_op'
    inlines = [PersonenInline]

    def get_email_display(self, obj):
        if obj.email_adressen:
            return ', '.join(obj.email_adressen[:2])  # Show first 2 emails
        return 'Geen email'
    get_email_display.short_description = 'Email Adressen'


@admin.register(Personen)
class PersonenAdmin(admin.ModelAdmin):
    list_display = ('persoon_id', 'persoon_naam', 'persoon_email', 'relatie', 'api_persoon_id')
    search_fields = ('persoon_naam', 'persoon_email', 'relatie__hoofdnaam')
    list_filter = ('relatie',)


@admin.register(AdviesAanvragen)
class AdviesAanvragenAdmin(admin.ModelAdmin):
    list_display = ('aanvraag_id', 'relatie', 'email_identifier', 'bestemmings_land_code', 'vertrekdatum', 'ingediend_op')
    list_filter = ('bestemmings_land_code', 'ingediend_op')
    search_fields = ('email_identifier', 'relatie__hoofdnaam')
    date_hierarchy = 'ingediend_op'


@admin.register(Contracten)
class ContractenAdmin(admin.ModelAdmin):
    list_display = ('contract_id', 'polisnummer', 'relatie', 'branche', 'datum_ingang', 'ts_aangemaakt')
    list_filter = ('branche', 'datum_ingang')
    search_fields = ('polisnummer', 'relatie__hoofdnaam', 'relatie__relatie_id')
    date_hierarchy = 'datum_ingang'


@admin.register(Polissen)
class PolissenAdmin(admin.ModelAdmin):
    list_display = ('polis_id', 'polisnummer', 'relatie', 'product_id', 'startdatum', 'totale_premie', 'status')
    list_filter = ('status', 'product_id')
    search_fields = ('polisnummer', 'relatie__hoofdnaam')
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
