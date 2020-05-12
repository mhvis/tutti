FROM python:3.8.2-alpine3.11

# Create a group and user to run our app
# ARG APP_USER=appuser
# RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}

# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

# Install dependencies
COPY Pipfile* /app/
RUN pip install --upgrade pip \
    && pip install --no-cache-dir pipenv \
    && cd /app/ \
    && pipenv lock --requirements > requirements.txt
RUN apk add --no-cache postgresql-dev python3-dev musl-dev \
    && pip install --no-cache-dir -r /app/requirements.txt \
    && pip install --no-cache-dir psycopg2 gunicorn

ADD . /app/

WORKDIR /app/

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "tutti.wsgi"]
