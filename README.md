# QLUIS

Het systeem van een heel aantal jaar terug heette volgens mij QLUIS, vandaar
deze naam, maar ik
heb geen idee waar het precies voor stond. TODO: naam verzinnen.

## Installation

Make sure that Pipenv is installed. Run the following commands:

* `pipenv install --dev`
* `pipenv shell`
* `python manage.py migrate`
* `python manage.py createsuperuser`

For deployments, it's easiest to add a `.env` file to specify a custom Django
settings module. In that module, you'll need to put the LDAP connection
credentials. Pipenv will automatically set the environment variables in that
file.

## Quickstart

* `ldapclone` command clones the LDAP directory into a fresh Django database.
* `ldappush` command does a one-way sync from Django to LDAP.

## Development commands

Assumes that the environment is set correctly using `pipenv shell`.
Alternatively use `pipenv run`.

* Run test server: `python manage.py runserver`
* Run unit tests: `python manage.py test`
* Lint code: `flake8`
