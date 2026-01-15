# Generated manually

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('comparator_app', '0007_add_omschrijving_to_contracten'),
    ]

    operations = [
        # First update the view to remove relatie_source column
        migrations.RunSQL(
            sql="""
                DROP VIEW IF EXISTS vw_contracten_readable;
                CREATE VIEW vw_contracten_readable AS
                SELECT
                    c.contract_id,
                    c.polisnummer,
                    c.branche,
                    c.datum_ingang,
                    c.ts_aangemaakt,
                    c.ts_gewijzigd,
                    c.relatie_id AS relatie_database_fk_id,
                    r.relatie_id AS relatie_assuportal_id,
                    r.hoofdnaam AS relatie_naam,
                    r.ts_aangemaakt AS relatie_ts_aangemaakt,
                    CASE WHEN r.relatie_id IS NOT NULL THEN TRUE ELSE FALSE END AS relatie_has_api_link,
                    COALESCE(r.hoofdnaam, 'Onbekend') || ' (ID: ' || COALESCE(r.relatie_id::text, 'Nieuw') || ')' AS relatie_volledige_weergave
                FROM contracten c
                JOIN relaties r ON c.relatie_id = r.id;
            """,
            reverse_sql="""
                DROP VIEW IF EXISTS vw_contracten_readable;
                CREATE VIEW vw_contracten_readable AS
                SELECT
                    c.contract_id,
                    c.polisnummer,
                    c.branche,
                    c.datum_ingang,
                    c.ts_aangemaakt,
                    c.ts_gewijzigd,
                    c.relatie_id AS relatie_database_fk_id,
                    r.relatie_id AS relatie_assuportal_id,
                    r.hoofdnaam AS relatie_naam,
                    r.ts_aangemaakt AS relatie_ts_aangemaakt,
                    r.source AS relatie_source,
                    COALESCE(r.hoofdnaam, 'Onbekend') || ' (ID: ' || COALESCE(r.relatie_id::text, 'Nieuw') || ')' AS relatie_volledige_weergave
                FROM contracten c
                JOIN relaties r ON c.relatie_id = r.id;
            """
        ),
        # Then remove the source field
        migrations.RemoveField(
            model_name='relaties',
            name='source',
        ),
    ]
