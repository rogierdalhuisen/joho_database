# Custom migration - recreate adviesaanvragen table
from django.db import migrations


def create_adviesaanvragen_table(apps, schema_editor):
    """Create the adviesaanvragen table from scratch."""
    schema_editor.execute("""
        CREATE TABLE IF NOT EXISTS adviesaanvragen (
            aanvraag_id SERIAL PRIMARY KEY,
            relatie_id INTEGER NOT NULL REFERENCES relaties(id) ON DELETE CASCADE,
            external_result_id VARCHAR(100) UNIQUE,
            form_id VARCHAR(50) DEFAULT '2',
            ingediend_op TIMESTAMP,
            referral_source VARCHAR(100),
            referral_medium VARCHAR(100),
            referral_campaign VARCHAR(200),
            aangemaakt_op TIMESTAMP DEFAULT NOW(),
            advies_voor_mezelf VARCHAR(50), aanhef VARCHAR(20), voorletters_roepnaam VARCHAR(100),
            achternaam VARCHAR(100), geboortedatum DATE, land_nationaliteit VARCHAR(100),
            email VARCHAR(254), telefoonnummer VARCHAR(50), vaste_woonplaats VARCHAR(200),
            geen_vaste_woonplaats BOOLEAN, meerdere_verzekerden VARCHAR(100),
            partner_naam VARCHAR(100), partner_geboortedatum DATE, partner_nationaliteit VARCHAR(100),
            kind1_naam VARCHAR(100), kind1_geboortedatum DATE, kind1_nationaliteit VARCHAR(100),
            kind2_naam VARCHAR(100), kind2_geboortedatum DATE, kind2_nationaliteit VARCHAR(100),
            kind3_naam VARCHAR(100), kind3_geboortedatum DATE, kind3_nationaliteit VARCHAR(100),
            kind4_naam VARCHAR(100), kind4_geboortedatum DATE, kind4_nationaliteit VARCHAR(100),
            anders_personen TEXT, situatie_type VARCHAR(200), bestemming_land VARCHAR(100),
            vertrekdatum DATE, uitschrijven_brp VARCHAR(50), huidig_woonland VARCHAR(100),
            advies_voor VARCHAR(200), hoofdreden_verblijf VARCHAR(200), toelichting_hoofdreden TEXT,
            verwachte_duur_verblijf VARCHAR(100), toelichting_duur TEXT, werk_omschrijving TEXT,
            plannen_omschrijving TEXT, salaris_uit_nederland VARCHAR(50), interesse_aov VARCHAR(50),
            loondienst_of_zelfstandig VARCHAR(50), eigen_onderneming_3jaar VARCHAR(50),
            bruto_jaarinkomen VARCHAR(100), aov_geen_offerte_reden TEXT,
            loon_doorbetaald_bij_ziekte VARCHAR(200), toelichting_uitkering TEXT,
            bruto_salaris_inkomen VARCHAR(100), salaris_per_maand_jaar VARCHAR(50),
            bouwplaats_of_offshore VARCHAR(50), bouwplaats_hoe_vaak VARCHAR(100),
            gevaarlijke_stoffen VARCHAR(50), toelichting_gevaarlijke_stoffen TEXT,
            interesse_internationale_aov VARCHAR(50), geen_interesse_aov_reden TEXT,
            functieomschrijving VARCHAR(200), type_werkzaamheden VARCHAR(100),
            verwacht_inkomen VARCHAR(100), inkomen_toelichting TEXT, interesse_zkv VARCHAR(50),
            zkv_geen_interesse_reden TEXT, zkv_dekkingsvariant VARCHAR(50),
            zkv_eigen_risico_voorkeur VARCHAR(50), zkv_eigen_risico_bedrag VARCHAR(50),
            zkv_periode VARCHAR(100), zkv_periode_omschrijving_motivatie TEXT,
            zkv_periode_omschrijving TEXT, huidige_verzekeraar VARCHAR(100),
            voorkeur_verzekeraar VARCHAR(100), medische_bijzonderheden VARCHAR(50),
            medische_bijzonderheden_toelichting TEXT, specifieke_wensen_zkv VARCHAR(50),
            wensen_toelichting TEXT, dekking_zwangerschap VARCHAR(50), zwangerschap_toelichting TEXT,
            andere_verzekeringen_interesse TEXT, overlijdensrisico_bedrag VARCHAR(100),
            overlijdensrisico_bedrag_anders VARCHAR(100), overlijdensrisico_bestemming TEXT,
            overlijdensrisico_bestemming_anders TEXT, sporten_activiteiten TEXT,
            sport_semiprofessioneel VARCHAR(50), sport_professioneel_omschrijving TEXT,
            huis_in_nederland VARCHAR(50), huis_type VARCHAR(50), woning_verhuurd VARCHAR(50),
            woning_eigen_gebruik VARCHAR(50), woning_verblijf_frequentie VARCHAR(200),
            woning_opmerkingen TEXT, hoe_gevonden VARCHAR(100), welke_website VARCHAR(200),
            naam_werkgever VARCHAR(200), hoe_gevonden_overig TEXT, eerder_contact_joho VARCHAR(50),
            eerder_contact_keuze VARCHAR(100), naam_contactpersoon VARCHAR(200),
            eerder_contact_anders TEXT, advies_vorm VARCHAR(50), raw_form_data JSONB
        );

        CREATE INDEX IF NOT EXISTS adviesaanvragen_email_idx ON adviesaanvragen(email);
        CREATE INDEX IF NOT EXISTS adviesaanvragen_external_result_id_idx ON adviesaanvragen(external_result_id);
        CREATE INDEX IF NOT EXISTS adviesaanvragen_relatie_id_idx ON adviesaanvragen(relatie_id);
        CREATE INDEX IF NOT EXISTS adviesaanvragen_bestemming_idx ON adviesaanvragen(bestemming_land);
        CREATE INDEX IF NOT EXISTS adviesaanvragen_interesse_zkv_idx ON adviesaanvragen(interesse_zkv);
    """)


def drop_adviesaanvragen_table(apps, schema_editor):
    """Drop the adviesaanvragen table."""
    schema_editor.execute("DROP TABLE IF EXISTS adviesaanvragen CASCADE;")


class Migration(migrations.Migration):

    dependencies = [
        ('comparator_app', '0002_alter_contracten_contract_id_and_more'),
    ]

    operations = [
        migrations.RunPython(create_adviesaanvragen_table, drop_adviesaanvragen_table),
    ]
