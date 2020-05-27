# Tutti

Q members admin.

## Quickstart

Make sure that Pipenv is installed. Run the following commands:

* `pipenv install --dev`
* `pipenv shell`
* `python manage.py migrate`
* `python manage.py createsuperuser`
* `python manage.py runserver`

You'll need to set the `DJANGO_SECRET_KEY` environment variable to some random
value for running the server. See e.g. [Pipenv `.env`](https://pipenv-fork.readthedocs.io/en/latest/advanced.html#automatic-loading-of-env).

## Development commands

Assumes that the environment is set correctly using `pipenv shell`.

* Run test server: `python manage.py runserver`. 
* Run unit tests: `python manage.py test`
* Lint code: `flake8`
* Create admin user: `python manage.py createsuperuser`
* Load sample fixtures: `python manage.py loaddata sampledata`.
* LDAP commands: `python manage.py ldapclone -h` and `python
  manage.py ldapsync -h`.


## Build CSS+JS

See `frontend/README.md`.

## On dependencies

Whenever you add a dependency to Pipfile, generate `requirements.txt`
afterwards: `pipenv lock -r > requirements.txt`.


## App structure

* `tutti`: project module, for project-wide settings.
* `members`: membership management app, stores people, groups and the rest.
  Also includes a custom admin site for branding.
* `pages`: homepage and base template.
* `ldapsync`: synchronization of the members data with an LDAP server.
* `aadsync`: synchronization of the member accounts and groups to Azure Active Directory.
* `oidc`: handle user login via OpenID Connect.
