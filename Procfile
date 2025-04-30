release: python3 manage.py makemigrations
release: python3 manage.py migrate
release: python3 manage.py collectstatic --noinput
release: python3 manage.py dumpdata bdd.json

web: gunicorn config.wsgi