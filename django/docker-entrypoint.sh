#!/usr/bin/env bash

set -e

cd /app

echo "Waiting for database to start..."
while !</dev/tcp/$DJANGO_DATABASE_HOST/$DJANGO_DATABASE_PORT; do
  sleep 1
done
echo "done"
echo

echo "Making database migrations..."
python manage.py makemigrations
echo "done"
echo

echo "Applying database migrations..."
python manage.py migrate
echo "done"
echo

echo "Collecting static files..."
python manage.py collectstatic --no-input
echo "done"
echo


if [ "$1" = 'uwsgi' ]; then
  [[ -S /tmp/sockets/wsgi.sock ]] && rm /tmp/sockets/wsgi.sock
  exec $@ \
    --master \
    --module=$DJANGO_APP_NAME.wsgi:application \
    --processes=$UWSGI_PROCESSES \
    --threads=$UWSGI_THREADS \
    --harakiri=$UWSGI_HARAKIRI \
    --max-requests=$UWSGI_MAX_REQUESTS \
    --socket=/tmp/sockets/wsgi.sock \
    --chmod-socket=666 \
    --http :80 \
    --check-static /app
fi

exec "$@"
