from django.core.management.base import BaseCommand
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
            help='Gebruik DETAIL endpoint voor Relaties (langzaam maar volledig met personen)'
        )

        parser.add_argument(
            '--max-pages',
            type=int,
            default=None,
            help='Maximaal aantal paginas om te verwerken (voor testen)'
        )

    def handle(self, *args, **options):
        """Voer de synchronisatie uit."""

        # Bepaal wat te syncen (default = all)
        sync_relaties_flag = options['relaties_only'] or options['all'] or (not options['contracten_only'])
        sync_contracten_flag = options['contracten_only'] or options['all'] or (not options['relaties_only'])

        page_size = options['page_size']
        use_detail = options['use_detail']
        max_pages = options['max_pages']

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
            self.stdout.write(f"  - Detail mode: ENABLED (met personen)")
        self.stdout.write("")

        # Sync Relaties
        if sync_relaties_flag:
            self.stdout.write(self.style.WARNING(">>> STAP 1: RELATIES SYNCHRONISEREN"))
            self.stdout.write("")

            try:
                success, errors = sync_relaties(
                    page_size=page_size,
                    use_detail=use_detail,
                    max_pages=max_pages
                )

                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS(f"✓ Relaties sync voltooid!"))
                self.stdout.write(f"  - Succesvol: {success}")
                self.stdout.write(f"  - Fouten: {errors}")
                self.stdout.write("")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ FOUT bij Relaties sync: {e}"))
                self.stdout.write("")
                return

        # Sync Contracten
        if sync_contracten_flag:
            self.stdout.write(self.style.WARNING(">>> STAP 2: CONTRACTEN SYNCHRONISEREN"))
            self.stdout.write("")

            try:
                success, errors, skipped = sync_contracten(
                    page_size=page_size,
                    max_pages=max_pages
                )

                self.stdout.write("")
                self.stdout.write(self.style.SUCCESS(f"✓ Contracten sync voltooid!"))
                self.stdout.write(f"  - Succesvol: {success}")
                self.stdout.write(f"  - Fouten: {errors}")
                self.stdout.write(f"  - Geskipt (geen relatie): {skipped}")
                self.stdout.write("")

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ FOUT bij Contracten sync: {e}"))
                self.stdout.write("")
                return

        # Footer
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  SYNCHRONISATIE COMPLEET"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
