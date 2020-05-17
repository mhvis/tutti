# Builder image
FROM python:3.8.2-alpine3.11 as builder

# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

# Compile dependencies
RUN apk update \
    && apk add --no-cache gcc postgresql-dev python3-dev musl-dev libffi-dev
# Build gunicorn+psycopg2 before building the rest so that they are not rebuilt when requirements change
RUN pip wheel --wheel-dir /wheels gunicorn psycopg2
COPY requirements.txt /app/requirements.txt
RUN pip wheel --wheel-dir /wheels -r /app/requirements.txt

# Compiled image
FROM python:3.8.2-alpine3.11

# Create app user+group
RUN addgroup -S app && adduser -S app -G app

# Setup static and media folders
RUN mkdir /appstatic /appmedia \
    && chown app:app /appstatic /appmedia
ENV DJANGO_STATIC_ROOT /appstatic
ENV DJANGO_MEDIA_ROOT /appmedia

# Install dependencies
RUN apk update \
    && apk add libpq
COPY --from=builder /wheels /wheels
COPY --from=builder /app/requirements.txt /app/requirements.txt
RUN pip install --no-cache /wheels/*

COPY ./entrypoint.sh /app/entrypoint.sh

COPY . /app/
WORKDIR /app/

USER app

ENTRYPOINT ["/app/entrypoint.sh"]
