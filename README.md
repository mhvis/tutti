# Tutti

Leden management systeem van Q.

## Installation

Make sure that Pipenv is installed. Run the following commands:

* `pipenv install --dev`
* `pipenv shell`
* `python manage.py migrate`
* `python manage.py createsuperuser`

You'll need a custom Django settings module for your local settings (e.g. LDAP
connection credentials). An easy way is to use a `.env` file, it will be
automatically picked up by Pipenv. See also:
[Django settings](https://docs.djangoproject.com/en/3.0/topics/settings/) and
[Pipenv `.env`](https://pipenv.pypa.io/en/latest/advanced/#automatic-loading-of-env).

## Quickstart

To load sample data: `python manage.py loaddata sampledata`

Available commands: `ldapclone`, `ldapsync`. Use `python manage.py <command name> -h` for details.

## Development commands

Assumes that the environment is set correctly using `pipenv shell`.
Alternatively use `pipenv run <command>`.

* Run test server: `python manage.py runserver`
* Run unit tests: `python manage.py test`
* Lint code: `flake8`


## Deployment

* [Use `pipenv sync` for dependencies.](https://pipenv.pypa.io/en/latest/advanced/#using-pipenv-for-deployments)
