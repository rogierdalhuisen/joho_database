"""
Django management command to import country-to-region mappings from Excel.

Usage:
    python manage.py import_country_regions path/to/excel_file.xlsx
"""

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from comparator_app.models import Landen, VerzekeringRegio, VerzekeringRegioLanden


class Command(BaseCommand):
    help = 'Import country-to-region mappings from an Excel file'

    def add_arguments(self, parser):
        parser.add_argument('excel_file', type=str, help='Path to the Excel file')
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing region mappings before import'
        )

    def generate_land_code(self, land_naam, existing_codes):
        """Generate a unique 3-letter country code from the country name."""
        # Remove special characters and spaces, take first 3 letters, uppercase
        clean_name = ''.join(c for c in land_naam if c.isalnum())
        base_code = clean_name[:3].upper()

        # Make it unique
        land_code = base_code
        counter = 1
        while land_code in existing_codes:
            land_code = f"{base_code[:2]}{counter}"
            counter += 1
            if counter > 99:
                # Fall back to incrementing the full code
                land_code = f"{base_code}{counter}"

        return land_code

    def import_landen(self, df):
        """Import all unique countries from the LAND column."""
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('STAP 1: Importeren van Landen'))
        self.stdout.write('='*60)

        # Get unique country names
        land_namen = df['LAND'].dropna().unique()
        land_namen = [str(naam).strip() for naam in land_namen if str(naam).strip()]

        self.stdout.write(f'Gevonden: {len(land_namen)} unieke landen in Excel bestand')

        # Get existing country codes to avoid duplicates
        existing_codes = set(Landen.objects.values_list('land_code', flat=True))

        stats = {
            'created': 0,
            'already_existed': 0,
        }

        for land_naam in sorted(land_namen):
            # Check if country already exists
            land = Landen.objects.filter(land_naam__iexact=land_naam).first()

            if land:
                stats['already_existed'] += 1
                self.stdout.write(f'  Bestaat al: {land.land_code} - {land_naam}')
            else:
                # Generate unique country code
                land_code = self.generate_land_code(land_naam, existing_codes)
                existing_codes.add(land_code)

                # Create the country
                land = Landen.objects.create(
                    land_code=land_code,
                    land_naam=land_naam
                )
                stats['created'] += 1
                self.stdout.write(self.style.SUCCESS(f'  Aangemaakt: {land_code} - {land_naam}'))

        self.stdout.write(f'\nLanden aangemaakt: {stats["created"]}')
        self.stdout.write(f'Landen bestonden al: {stats["already_existed"]}')

        return stats

    def handle(self, *args, **options):
        excel_file = options['excel_file']

        try:
            # Read the Excel file
            df = pd.read_excel(excel_file)
        except FileNotFoundError:
            raise CommandError(f'Excel bestand niet gevonden: {excel_file}')
        except Exception as e:
            raise CommandError(f'Fout bij lezen Excel bestand: {e}')

        # Validate that the file has the expected structure
        if 'LAND' not in df.columns:
            raise CommandError('Excel bestand moet een "LAND" kolom bevatten')

        # Get all verzekeraar columns (exclude the LAND column)
        verzekeraar_columns = [col for col in df.columns if col != 'LAND']

        if not verzekeraar_columns:
            raise CommandError('Geen verzekeraar kolommen gevonden in Excel bestand')

        self.stdout.write(f'Gevonden: {len(verzekeraar_columns)} verzekeraars: {", ".join(verzekeraar_columns)}')
        self.stdout.write(f'Gevonden: {len(df)} landen om te verwerken')

        # Clear existing mappings if requested
        if options['clear']:
            self.stdout.write(self.style.WARNING('Bestaande regio koppelingen verwijderen...'))
            VerzekeringRegioLanden.objects.all().delete()
            VerzekeringRegio.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Bestaande koppelingen verwijderd'))

        # STAP 1: Import landen from LAND column
        landen_stats = self.import_landen(df)

        # STAP 2: Import region mappings
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('STAP 2: Importeren van Regio Koppelingen'))
        self.stdout.write('='*60)

        # Statistics
        stats = {
            'verzekering_regios_created': 0,
            'verzekering_regios_found': 0,
            'landen_matched': 0,
            'landen_not_found': 0,
            'mappings_created': 0,
            'skipped_nvt': 0,
        }

        # Process each verzekeraar column
        for verzekeraar_naam in verzekeraar_columns:
            self.stdout.write(f'\nVerwerken verzekeraar: {verzekeraar_naam}')

            # Track regions for this verzekeraar to avoid duplicates
            verzekeraar_regios_cache = {}

            # Process each country for this verzekeraar
            for index, row in df.iterrows():
                land_naam = str(row['LAND']).strip()
                regio_naam = str(row[verzekeraar_naam]).strip()

                # Skip if region is NVT (not applicable) or empty
                if regio_naam.upper() in ['NVT', 'NAN', ''] or pd.isna(row[verzekeraar_naam]):
                    stats['skipped_nvt'] += 1
                    continue

                # Try to find the country in the database
                # First try exact match on land_naam
                land = Landen.objects.filter(land_naam__iexact=land_naam).first()

                if not land:
                    # Try to find by partial match (in case of naming differences)
                    land = Landen.objects.filter(land_naam__icontains=land_naam).first()

                if not land:
                    self.stdout.write(
                        self.style.WARNING(f'  Land niet gevonden: {land_naam}')
                    )
                    stats['landen_not_found'] += 1
                    continue

                stats['landen_matched'] += 1

                # Get or create the VerzekeringRegio
                # Use a cache key combining verzekeraar and regio names
                cache_key = f"{verzekeraar_naam}::{regio_naam}"

                if cache_key not in verzekeraar_regios_cache:
                    verzekering_regio, regio_created = VerzekeringRegio.objects.get_or_create(
                        verzekeraar_naam=verzekeraar_naam,
                        regio_naam=regio_naam,
                        defaults={'status': 'actief'}
                    )
                    verzekeraar_regios_cache[cache_key] = verzekering_regio

                    if regio_created:
                        stats['verzekering_regios_created'] += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'  Nieuwe regio aangemaakt: {verzekeraar_naam} - {regio_naam}'
                        ))
                    else:
                        stats['verzekering_regios_found'] += 1
                else:
                    verzekering_regio = verzekeraar_regios_cache[cache_key]

                # Create the country-to-region mapping (if it doesn't exist)
                mapping, mapping_created = VerzekeringRegioLanden.objects.get_or_create(
                    verzekering_regio=verzekering_regio,
                    land_code=land
                )

                if mapping_created:
                    stats['mappings_created'] += 1

        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('EINDOVERZICHT'))
        self.stdout.write('='*60)
        self.stdout.write('\nLanden:')
        self.stdout.write(f"  Aangemaakt: {landen_stats['created']}")
        self.stdout.write(f"  Bestonden al: {landen_stats['already_existed']}")
        self.stdout.write('\nVerzekering Regios:')
        self.stdout.write(f"  Aangemaakt: {stats['verzekering_regios_created']}")
        self.stdout.write(f"  Gevonden: {stats['verzekering_regios_found']}")
        self.stdout.write('\nRegio Koppelingen:')
        self.stdout.write(f"  Landen gekoppeld: {stats['landen_matched']}")
        if stats['landen_not_found'] > 0:
            self.stdout.write(self.style.WARNING(f"  Landen niet gevonden: {stats['landen_not_found']}"))
        self.stdout.write(f"  Koppelingen aangemaakt: {stats['mappings_created']}")
        self.stdout.write(f"  Overgeslagen (NVT/leeg): {stats['skipped_nvt']}")

        if stats['landen_not_found'] > 0:
            self.stdout.write('\n' + self.style.WARNING(
                'Sommige landen konden niet worden gekoppeld. Dit kan komen door encoding problemen of typfouten.'
            ))
