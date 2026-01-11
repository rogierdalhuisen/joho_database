python manage.py sync_assuportal_data --relaties-only --use-detail --page-size=50  
python manage.py sync_assuportal_data --contracten-only --page-size=50

python manage.py makemigrations  
python manage.py migrate

Test E-grip Sync (Dry-Run)

# Preview first 10 results without saving

python src/manage.py sync_egrip_data --dry-run --max-results 10

Test Assuportal Sync (Dry-Run)

# Preview first 2 pages without saving

python src/manage.py sync_assuportal_data --dry-run --max-pages 2

Run Real Sync (After Testing)

# E-grip - real sync

python src/manage.py sync_egrip_data --max-results 10

# Assuportal - real sync

python src/manage.py sync_assuportal_data --max-pages 2
