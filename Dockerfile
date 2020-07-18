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


# Builder image for creating venv
FROM python:3.8-alpine as builder

# Install build requirements, create virtualenv
RUN apk update \
    && apk add --no-cache gcc g++ postgresql-dev python3-dev musl-dev libffi-dev \
    && python -m venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Build+install app dependencies
RUN pip install --upgrade pip setuptools wheel \
    && pip install gunicorn psycopg2
COPY requirements.txt .
RUN pip install -r requirements.txt


# Compiled image
FROM python:3.8-alpine

# Create app user+group
RUN addgroup -S app && adduser -S app -G app

# Copy virtualenv and apply
RUN apk update \
    && apk add libpq
COPY --from=builder /app/venv /app/venv
ENV PATH="/app/venv/bin:$PATH"

# Copy the app
COPY . /app/src
WORKDIR /app/src

# Some Python settings
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1

# Setup static and media folders
# A secret key needs to be set otherwise collectstatic fails
ENV DJANGO_STATIC_ROOT=/app/static DJANGO_MEDIA_ROOT=/app/media DJANGO_SECRET_KEY=dummy DJANGO_WHITENOISE=1
RUN mkdir /app/static /app/media \
    && chown app:app /app/media \
    && python manage.py collectstatic --noinput
# Unset secret key
ENV DJANGO_SECRET_KEY=

# Bake build date into src directory, will be read by the app
RUN date -I > builddate.txt

USER app

# By default launch gunicorn on :8000
CMD ["gunicorn", "-w", "3", "-b", "0.0.0.0:8000", "tutti.wsgi"]
