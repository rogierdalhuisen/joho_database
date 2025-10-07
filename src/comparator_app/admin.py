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
    list_display = ('verzekeraar_id', 'naam', 'status')
    list_filter = ('status',)
    search_fields = ('naam',)


@admin.register(VerzekeraarRegio)
class VerzekeraarRegioAdmin(admin.ModelAdmin):
    list_display = ('verzekeraar_regio_id', 'verzekeraar_id', 'regio_naam')
    list_filter = ('verzekeraar_id',)
    search_fields = ('regio_naam',)


@admin.register(Producten)
class ProductenAdmin(admin.ModelAdmin):
    list_display = ('product_id', 'naam', 'verzekeraar_id', 'policy_type', 'max_leeftijd_aanvraag', 'max_leeftijd_dekking')
    list_filter = ('verzekeraar_id', 'policy_type')
    search_fields = ('naam', 'beschrijving')


@admin.register(ProductModules)
class ProductModulesAdmin(admin.ModelAdmin):
    list_display = ('product_module_id', 'product_id', 'module_naam', 'is_verplicht')
    list_filter = ('product_id', 'is_verplicht')
    search_fields = ('module_naam',)


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


@admin.register(DekkingsItems)
class DekkingsItemsAdmin(admin.ModelAdmin):
    list_display = ('item_id', 'item_naam')
    search_fields = ('item_naam',)


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


# Simple registration for mapping tables
admin.site.register(VerzekeraarRegioLanden)
admin.site.register(ProductTargetDoelgroepen)
admin.site.register(ItemCategorieMapping)
