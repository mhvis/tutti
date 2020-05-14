FROM python:3.8.2-alpine3.11

# Create a group and user to run our app
# ARG APP_USER=appuser
# RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}

# Prevents Python from writing pyc files to disc (equivalent to python -B option)
ENV PYTHONDONTWRITEBYTECODE 1
# Prevents Python from buffering stdout and stderr (equivalent to python -u option)
ENV PYTHONUNBUFFERED 1

# Install dependencies
RUN apk add --no-cache gcc postgresql-dev python3-dev musl-dev libffi-dev \
    && pip install --upgrade pip \
    && pip install --no-cache-dir gunicorn psycopg2
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

ADD . /app/

WORKDIR /app/

CMD ["gunicorn", "--bind", ":8000", "--workers", "3", "tutti.wsgi"]
