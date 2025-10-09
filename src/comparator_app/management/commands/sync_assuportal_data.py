from django.core.management.base import BaseCommand
from src.comparator_app.api_assuportal import fetch_new_data_from_assuportal, process_and_save_record   

class Command(BaseCommand):
    help = 'Haalt nieuwe data op van de Assuportal API en synchroniseert deze.'

    def handle(self, *args, **options):
        self.stdout.write("Starten van Assuportal synchronisatie...")
        
        # Stap 1: Haal data op via de API
        api_records = fetch_data_from_assuportal()
        if not api_records:
            self.stdout.write(self.style.WARNING("Geen nieuwe records gevonden of API-call mislukt."))
            return

        self.stdout.write(f"{len(api_records)} records gevonden, starten met verwerking...")

        # Stap 2: Verwerk de opgehaalde data
        success_count, error_count = process_and_save_api_data(api_records)

        # Stap 3: Rapporteer het resultaat
        self.stdout.write(self.style.SUCCESS(f"\nSynchronisatie voltooid."))
        self.stdout.write(f"Succesvol verwerkt: {success_count} records.")
        self.stdout.write(f"Mislukt: {error_count} records.")