from django.core.management.base import BaseCommand
from comparator_app.api_egrip import sync_egrip_formulieren


class Command(BaseCommand):
    help = 'Synchroniseert AdviesAanvragen van de E-grip API naar de database.'

    def add_arguments(self, parser):
        """Voeg command-line argumenten toe."""

        parser.add_argument(
            '--form-id',
            type=str,
            default='2',
            help='E-grip formulier ID (default: 2)'
        )

        parser.add_argument(
            '--max-results',
            type=int,
            default=None,
            help='Maximaal aantal results om te verwerken (voor testen)'
        )

        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without committing to database (DRY RUN mode)'
        )

    def handle(self, *args, **options):
        """Voer de synchronisatie uit."""

        form_id = options['form_id']
        max_results = options['max_results']
        dry_run = options['dry_run']

        # Header
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  E-GRIP FORMULIEREN SYNCHRONISATIE"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write("")

        # Configuratie
        self.stdout.write("Configuratie:")
        self.stdout.write(f"  - Formulier ID: {form_id}")
        if max_results:
            self.stdout.write(f"  - Max results: {max_results} (TEST MODE)")
        else:
            self.stdout.write(f"  - Max results: Alle (PRODUCTIE)")

        if dry_run:
            self.stdout.write(self.style.WARNING(f"  - DRY RUN: Enabled (geen wijzigingen worden opgeslagen)"))
        else:
            self.stdout.write(f"  - DRY RUN: Disabled (wijzigingen worden opgeslagen)")
        self.stdout.write("")

        # Dry run warning
        if dry_run:
            self.stdout.write(self.style.WARNING("⚠ DRY RUN MODE: Geen data wordt opgeslagen in de database"))
            self.stdout.write("")

        # Sync
        self.stdout.write(self.style.WARNING(">>> SYNCHRONISEREN ADVIESAANVRAGEN"))
        self.stdout.write("")

        try:
            success, errors, skipped = sync_egrip_formulieren(
                form_id=form_id,
                max_results=max_results,
                dry_run=dry_run
            )

            self.stdout.write("")
            if dry_run:
                self.stdout.write(self.style.SUCCESS(f"✓ E-grip DRY RUN voltooid!"))
            else:
                self.stdout.write(self.style.SUCCESS(f"✓ E-grip sync voltooid!"))

            self.stdout.write(f"  - Succesvol: {success}")
            self.stdout.write(f"  - Geskipt (duplicaten): {skipped}")
            self.stdout.write(f"  - Fouten: {errors}")
            self.stdout.write("")

            if errors > 0:
                self.stdout.write(self.style.WARNING(f"⚠ Let op: {errors} fouten tijdens sync. Check de logs."))
                self.stdout.write("")

            if dry_run:
                self.stdout.write(self.style.NOTICE("ℹ Dit was een DRY RUN. Voer het commando zonder --dry-run uit om wijzigingen op te slaan."))
                self.stdout.write("")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ FOUT bij E-grip sync: {e}"))
            self.stdout.write("")
            import traceback
            self.stdout.write(traceback.format_exc())
            return

        # Footer
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("  SYNCHRONISATIE COMPLEET"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
