# Docker image for Tutti with static files baked in.
#
#
# Static files are handled by WhiteNoise. Media files are stored in /app/media,
# so that folder should be mounted as a Docker volume.
#
# The default command runs the gunicorn server on port 8000. You need to run
# migrate yourself, e.g. using `docker run tutti python manage.py migrate
# --noinput`.
#
# For environment variables that need to be set, see settings.py.
FROM python:3.8-buster

# Install dependencies
WORKDIR /app/src
RUN pip install --no-cache-dir gunicorn psycopg2
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app
COPY . .

# Some Python settings
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Setup static and media folders
# A secret key needs to be set otherwise collectstatic fails
ENV DJANGO_STATIC_ROOT=/app/static DJANGO_MEDIA_ROOT=/app/media DJANGO_SECRET_KEY=dummy DJANGO_WHITENOISE=1
RUN mkdir /app/static /app/media && python manage.py collectstatic --noinput
# Unset secret key
ENV DJANGO_SECRET_KEY=

# Bake build date into src directory, will be read by the app
RUN date -I > builddate.txt

# Create user
RUN useradd -u 1001 appuser && chown appuser /app/media
USER appuser

# By default launch gunicorn on :8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "tutti.wsgi"]
