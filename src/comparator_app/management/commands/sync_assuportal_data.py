from django.core.management.base import BaseCommand, CommandError
from datetime import datetime
from comparator_app.api_assuportal import sync_relaties, sync_contracten


class Command(BaseCommand):
    help = 'Synchroniseert data van de Assuportal API naar de database.'

    def add_arguments(self, parser):
        """Voeg command-line argumenten toe."""

        # Sync mode
        parser.add_argument(
            '--relaties-only',
            action='store_true',
            help='Synchroniseer alleen Relaties (niet Contracten)'
        )

        parser.add_argument(
            '--contracten-only',
            action='store_true',
            help='Synchroniseer alleen Contracten (niet Relaties)'
        )

        parser.add_argument(
            '--all',
            action='store_true',
            help='Synchroniseer zowel Relaties als Contracten (default)'
        )

        # Options
        parser.add_argument(
            '--page-size',
            type=int,
            default=50,
            help='Aantal records per API pagina (default: 50)'
        )

        parser.add_argument(
            '--use-detail',
            action='store_true',
            help='Gebruik DETAIL endpoint voor Relaties en Contracten (langzaam maar volledig met alle velden)'
        )

        parser.add_argument(
            '--no-detail',
            action='store_true',
            help='Gebruik ALLEEN LIST endpoint (sneller maar mogelijk incomplete data)'
        )

        parser.add_argument(
            '--max-pages',
            type=int,
            default=None,
            help='Maximaal aantal paginas om te verwerken (voor testen)'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without committing to database (DRY RUN mode)'
        )

        # Date filters
        parser.add_argument(
            '--datum-van',
            type=str,
            default=None,
            help='Filter: alleen records aangemaakt/gewijzigd vanaf deze datum (format: YYYY-MM-DD, bijv. 2015-11-11)'
        )

        parser.add_argument(
            '--datum-tot',
            type=str,
            default=None,
            help='Filter: alleen records aangemaakt/gewijzigd tot deze datum (format: YYYY-MM-DD, bijv. 2015-11-12)'
        )

    def handle(self, *args, **options):
        """Voer de synchronisatie uit."""

        # Bepaal wat te syncen (default = all)
        sync_relaties_flag = options['relaties_only'] or options['all'] or (not options['contracten_only'])
        sync_contracten_flag = options['contracten_only'] or options['all'] or (not options['relaties_only'])

        page_size = options['page_size']
        use_detail = options['use_detail'] or not options['no_detail']  # Default True unless --no-detail specified
        max_pages = options['max_pages']
        dry_run = options['dry_run']

        # Parse date filters
        datum_van = None
        datum_tot = None

        if options['datum_van']:
            try:
                datum_van = datetime.strptime(options['datum_van'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError(f"Ongeldige datum voor --datum-van: {options['datum_van']}. Gebruik format YYYY-MM-DD")

        if options['datum_tot']:
            try:
                datum_tot = datetime.strptime(options['datum_tot'], '%Y-%m-%d').date()
            except ValueError:
                raise CommandError(f"Ongeldige datum voor --datum-tot: {options['datum_tot']}. Gebruik format YYYY-MM-DD")

        # Validate date range
        if datum_van and datum_tot and datum_van > datum_tot:
            raise CommandError("--datum-van moet voor --datum-tot liggen")

        # Header
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  ASSUPORTAL DATA SYNCHRONISATIE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Configuratie
        self.stdout.write("Configuratie:")
        self.stdout.write(f"  - Pagina grootte: {page_size}")
        if max_pages:
            self.stdout.write(f"  - Max paginas: {max_pages} (TEST MODE)")
        if use_detail:
            self.stdout.write(f"  - Detail mode: ENABLED (volledige data voor relaties + contracten)")
        else:
            self.stdout.write(f"  - Detail mode: DISABLED (alleen list data, mogelijk incomplete velden)")

        # Date filter info
        if datum_van or datum_tot:
            self.stdout.write(f"  - Datum filter: {datum_van or 'begin'} tot {datum_tot or 'eind'}")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"  - DRY RUN: Enabled (geen wijzigingen worden opgeslagen)"))
        else:
            self.stdout.write(f"  - DRY RUN: Disabled (wijzigingen worden opgeslagen)")
        self.stdout.write("")

        # Dry run warning
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠ DRY RUN MODE: Geen data wordt opgeslagen in de database"))
            self.stdout.write("")

        # Sync Relaties
        if sync_relaties_flag:
            self.stdout.write(self.style.WARNING(">>> STAP 1: RELATIES SYNCHRONISEREN"))
            self.stdout.write("")

            try:
                success, errors = sync_relaties(
                    page_size=page_size,
                    use_detail=use_detail,
                    max_pages=max_pages,
                    dry_run=dry_run,
                    datum_van=datum_van,
                    datum_tot=datum_tot
                )

                self.stdout.write("")
                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f"✓ Relaties DRY RUN voltooid!"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✓ Relaties sync voltooid!"))

                self.stdout.write(f"  - Succesvol: {success}")
                self.stdout.write(f"  - Fouten: {errors}")
                self.stdout.write("")

                if errors > 0:
                    self.stdout.write(self.style.WARNING(f"⚠ Let op: {errors} fouten tijdens Relaties sync. Check de logs."))
                    self.stdout.write("")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ FOUT bij Relaties sync: {e}"))
                self.stdout.write("")
                import traceback
                self.stdout.write(traceback.format_exc())
                return

        # Sync Contracten
        if sync_contracten_flag:
            self.stdout.write(self.style.WARNING(">>> STAP 2: CONTRACTEN SYNCHRONISEREN"))
            self.stdout.write("")

            try:
                success, errors, skipped = sync_contracten(
                    page_size=page_size,
                    use_detail=use_detail,
                    max_pages=max_pages,
                    dry_run=dry_run,
                    datum_van=datum_van,
                    datum_tot=datum_tot
                )

                self.stdout.write("")
                if dry_run:
                    self.stdout.write(self.style.SUCCESS(f"✓ Contracten DRY RUN voltooid!"))
                else:
                    self.stdout.write(self.style.SUCCESS(f"✓ Contracten sync voltooid!"))

                self.stdout.write(f"  - Succesvol: {success}")
                self.stdout.write(f"  - Fouten: {errors}")
                self.stdout.write(f"  - Geskipt (geen relatie): {skipped}")
                self.stdout.write("")

                if errors > 0:
                    self.stdout.write(self.style.WARNING(f"⚠ Let op: {errors} fouten tijdens Contracten sync. Check de logs."))
                    self.stdout.write("")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ FOUT bij Contracten sync: {e}"))
                self.stdout.write("")
                import traceback
                self.stdout.write(traceback.format_exc())
                return

        # Dry run reminder
        if dry_run:
            self.stdout.write(self.style.NOTICE("ℹ Dit was een DRY RUN. Voer het commando zonder --dry-run uit om wijzigingen op te slaan."))
            self.stdout.write("")

        # Footer
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  SYNCHRONISATIE COMPLEET"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
