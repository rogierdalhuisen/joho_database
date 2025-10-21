from django.contrib import admin
from .models import (
    Landen,
    Klanten,
    Aanvragen,
    Verzekeraars,
    VerzekeraarRegio,
    VerzekeraarRegioLanden,
    Doelgroepen,
    Producten,
    ProductTargetDoelgroepen,
    ProductModules,
    DocumentChunk,
    DekkingsNiveaus,
    DekkingsCategorien,
    DekkingsItems,
    ItemCategorieMapping,
    DekkingsItemDetails,
    PremieParameters,
    ParameterOpties,
    Premies,
    PremieParameterMapping,
    Polissen,
    PolisModules,
    PolisOpties,
    BusinessRules
)


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


@admin.register(PolisModules)
class PolisModulesAdmin(admin.ModelAdmin):
    list_display = ('polis_module_id', 'polis_id', 'product_module_id', 'level_id')
    list_filter = ('product_module_id', 'level_id')


@admin.register(PolisOpties)
class PolisOptiesAdmin(admin.ModelAdmin):
    list_display = ('polis_optie_id', 'polis_id', 'option_id')
    list_filter = ('polis_id',)


# --- Product & Verzekeraar Admin ---
@admin.register(Verzekeraars)
class VerzekeraarsAdmin(admin.ModelAdmin):
    list_display = ('verzekeraar_id', 'naam', 'status', 'get_products_count', 'get_regions_count')
    list_filter = ('status',)
    search_fields = ('naam',)

    def get_products_count(self, obj):
        count = obj.products.count()
        if count == 0:
            return '⚠️ 0 producten'
        return f'✅ {count} producten'
    get_products_count.short_description = 'Producten'

    def get_regions_count(self, obj):
        count = obj.regios.count()
        if count == 0:
            return '⚠️ 0 regio\'s'
        return f'✅ {count} regio\'s'
    get_regions_count.short_description = 'Regio\'s'


@admin.register(VerzekeraarRegio)
class VerzekeraarRegioAdmin(admin.ModelAdmin):
    list_display = ('verzekeraar_regio_id', 'verzekeraar_id', 'regio_naam')
    list_filter = ('verzekeraar_id',)
    search_fields = ('regio_naam',)


class ProductModulesInline(admin.TabularInline):
    model = ProductModules
    extra = 0
    fields = ('module_naam', 'is_verplicht', 'beschrijving')
    show_change_link = True


class ProductTargetDoelgroepenInline(admin.TabularInline):
    model = ProductTargetDoelgroepen
    extra = 1
    verbose_name = 'Doelgroep'
    verbose_name_plural = 'Doelgroepen'


@admin.register(Producten)
class ProductenAdmin(admin.ModelAdmin):
    list_display = (
        'product_id',
        'naam',
        'verzekeraar_id',
        'policy_type',
        'get_modules_count',
        'get_doelgroepen_count',
        'get_coverage_status',
        'get_premium_status',
        'max_leeftijd_aanvraag',
        'max_leeftijd_dekking'
    )
    list_filter = ('verzekeraar_id', 'policy_type')
    search_fields = ('naam', 'beschrijving')
    inlines = [ProductTargetDoelgroepenInline, ProductModulesInline]

    def get_modules_count(self, obj):
        count = obj.product_modules.count()
        if count == 0:
            return '❌ 0 modules'
        return f'✅ {count} modules'
    get_modules_count.short_description = 'Modules'

    def get_doelgroepen_count(self, obj):
        count = obj.target_doelgroep_mappings.count()
        if count == 0:
            return '⚠️ Geen'
        return f'✅ {count}'
    get_doelgroepen_count.short_description = 'Doelgroepen'

    def get_coverage_status(self, obj):
        # Check if there are any coverage details for this product's modules
        modules = obj.product_modules.all()
        total_modules = modules.count()
        if total_modules == 0:
            return '⚠️ Geen modules'

        modules_with_coverage = 0
        for module in modules:
            if module.dekking_details.exists():
                modules_with_coverage += 1

        if modules_with_coverage == 0:
            return '❌ Geen dekking'
        elif modules_with_coverage < total_modules:
            return f'⚠️ {modules_with_coverage}/{total_modules}'
        return f'✅ {modules_with_coverage}/{total_modules}'
    get_coverage_status.short_description = 'Dekking ingevuld'

    def get_premium_status(self, obj):
        # Check if there are premiums for this product's modules
        modules = obj.product_modules.all()
        total_modules = modules.count()
        if total_modules == 0:
            return '⚠️ Geen modules'

        modules_with_premiums = 0
        for module in modules:
            if module.premies.exists():
                modules_with_premiums += 1

        if modules_with_premiums == 0:
            return '❌ Geen premies'
        elif modules_with_premiums < total_modules:
            return f'⚠️ {modules_with_premiums}/{total_modules}'
        return f'✅ {modules_with_premiums}/{total_modules}'
    get_premium_status.short_description = 'Premies ingevuld'


@admin.register(ProductModules)
class ProductModulesAdmin(admin.ModelAdmin):
    list_display = (
        'product_module_id',
        'product_id',
        'module_naam',
        'is_verplicht',
        'get_coverage_items_count',
        'get_premium_params_count',
        'get_premiums_count'
    )
    list_filter = ('product_id', 'is_verplicht')
    search_fields = ('module_naam', 'beschrijving')

    def get_coverage_items_count(self, obj):
        count = obj.dekking_details.count()
        if count == 0:
            return '❌ 0 items'
        return f'✅ {count} items'
    get_coverage_items_count.short_description = 'Dekking items'

    def get_premium_params_count(self, obj):
        count = obj.premie_parameters.count()
        if count == 0:
            return '⚠️ 0'
        return f'✅ {count}'
    get_premium_params_count.short_description = 'Parameters'

    def get_premiums_count(self, obj):
        count = obj.premies.count()
        if count == 0:
            return '❌ 0 premies'
        return f'✅ {count} premies'
    get_premiums_count.short_description = 'Premies'


@admin.register(DocumentChunk)
class DocumentChunkAdmin(admin.ModelAdmin):
    list_display = ('chunk_id', 'product_id', 'product_module_id')
    list_filter = ('product_id', 'product_module_id')
    search_fields = ('content',)


# --- Dekking Admin ---
@admin.register(DekkingsNiveaus)
class DekkingsNiveausAdmin(admin.ModelAdmin):
    list_display = ('niveau_id', 'niveau_name', 'niveau_rank')
    ordering = ('niveau_rank',)


@admin.register(DekkingsCategorien)
class DekkingsCategorienAdmin(admin.ModelAdmin):
    list_display = ('categorie_id', 'categorie_naam', 'parent_categorie_id')
    list_filter = ('parent_categorie_id',)
    search_fields = ('categorie_naam',)


class ItemCategorieMappingInline(admin.TabularInline):
    model = ItemCategorieMapping
    extra = 1
    verbose_name = 'Categorie'
    verbose_name_plural = 'Categorieën'


@admin.register(DekkingsItems)
class DekkingsItemsAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'item_naam', 'get_categories')
    search_fields = ('item_naam',)
    inlines = [ItemCategorieMappingInline]

    def get_categories(self, obj):
        return ", ".join([mapping.categorie_id.categorie_naam for mapping in obj.item_categorie_mappings.all()])
    get_categories.short_description = 'Categorieën'


@admin.register(DekkingsItemDetails)
class DekkingsItemDetailsAdmin(admin.ModelAdmin):
    list_display = ('detail_id', 'niveau_id', 'item_id', 'product_module_id', 'dekkings_type', 'numerieke_waarde', 'valuta')
    list_filter = ('dekkings_type', 'product_module_id__product_id', 'niveau_id')
    search_fields = ('voorwaarden_tekst',)


# --- Premie Admin ---
@admin.register(PremieParameters)
class PremieParametersAdmin(admin.ModelAdmin):
    list_display = ('parameter_id', 'product_module_id', 'parameter_naam')
    list_filter = ('product_module_id__product_id',)
    search_fields = ('parameter_naam',)


@admin.register(ParameterOpties)
class ParameterOptiesAdmin(admin.ModelAdmin):
    list_display = ('optie_id', 'parameter_id', 'optie_waarde_tekst', 'min_waarde', 'max_waarde')
    list_filter = ('parameter_id',)
    search_fields = ('optie_waarde_tekst',)


@admin.register(Premies)
class PremiesAdmin(admin.ModelAdmin):
    list_display = ('premie_id', 'product_module_id', 'level_id', 'premie', 'valuta', 'termijn')
    list_filter = ('product_module_id__product_id', 'level_id', 'termijn')


@admin.register(PremieParameterMapping)
class PremieParameterMappingAdmin(admin.ModelAdmin):
    list_display = ('premie_id', 'optie_id')
    list_filter = ('premie_id__product_module_id__product_id',)


# --- Support Tables Admin ---
@admin.register(Landen)
class LandenAdmin(admin.ModelAdmin):
    list_display = ('land_code', 'land_naam')
    search_fields = ('land_naam', 'land_code')


@admin.register(Doelgroepen)
class DoelgroepenAdmin(admin.ModelAdmin):
    list_display = ('doelgroep_id', 'doelgroep_naam')
    search_fields = ('doelgroep_naam',)


@admin.register(BusinessRules)
class BusinessRulesAdmin(admin.ModelAdmin):
    list_display = ('rule_id', 'scope_entity', 'scope_id', 'rule_type')
    list_filter = ('scope_entity', 'rule_type')
    search_fields = ('message',)


# Mapping tables with better displays
@admin.register(VerzekeraarRegioLanden)
class VerzekeraarRegioLandenAdmin(admin.ModelAdmin):
    list_display = ('verzekeraar_regio_id', 'land_code')
    list_filter = ('verzekeraar_regio_id__verzekeraar_id',)
    search_fields = ('land_code__land_naam',)


@admin.register(ProductTargetDoelgroepen)
class ProductTargetDoelgroepenAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'doelgroep_id')
    list_filter = ('product_id', 'doelgroep_id')
    search_fields = ('product_id__naam', 'doelgroep_id__doelgroep_naam')


@admin.register(ItemCategorieMapping)
class ItemCategorieMappingAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'categorie_id')
    list_filter = ('categorie_id',)
    search_fields = ('item_id__item_naam', 'categorie_id__categorie_naam')
