from django.core.management.base import BaseCommand
from src.comparator_app.api_grip import fetch_new_data_from_grip, process_and_save_record

class Command(BaseCommand):
    help = 'Haalt nieuwe klantdata op van de Grip API en synchroniseert deze.'

    def handle(self, *args, **options):
        self.stdout.write("Starting Grip data synchronization...")
        
        new_records = fetch_new_data_from_grip()

        if not new_records:
            self.stdout.write(self.style.WARNING("No new records found or API call failed."))
            return

        success_count = 0
        error_count = 0

        for record in new_records:
            record_id = record.get('id', 'N/A') # Gebruik een uniek ID uit de data
            success, errors = process_and_save_record(record)
            
            if success:
                success_count += 1
                self.stdout.write(self.style.SUCCESS(f"Successfully processed record {record_id}"))
            else:
                error_count += 1
                self.stderr.write(self.style.ERROR(f"Failed to process record {record_id}: {errors}"))

        self.stdout.write(self.style.SUCCESS(f"\nSynchronization complete."))
        self.stdout.write(f"Successfully processed: {success_count} records.")
        self.stdout.write(f"Failed to process: {error_count} records.")