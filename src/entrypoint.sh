echo "Running entrypoint script..."
python manage.py migrate

echo "Starting server..."
python manage.py runserver 0.0.0.0:8000 # in production use gunicorn, wait noise, static files etc.