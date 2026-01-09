python manage.py sync_assuportal_data --relaties-only --use-detail --page-size=50  
python manage.py sync_assuportal_data --contracten-only --page-size=50

python manage.py makemigrations  
python manage.py migrate
