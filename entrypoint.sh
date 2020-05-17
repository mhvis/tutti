#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

python manage.py migrate

# If a static root is set, run collectstatic
if [ -n "$DJANGO_STATIC_ROOT" ]
then
  python manage.py collectstatic --noinput
fi

exec "$@"
