# Tutti

Q members admin.

## Quickstart

* Create and activate a virtual environment (`python3 -m venv venv`)
* Copy `.env.example` to `.env` and adjust as necessary
* `pip install -r requirements.txt -r dev-requirements.txt`
* `python manage.py migrate`
* `python manage.py createsuperuser`
* `python manage.py runserver`

## Useful commands

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

To add a new dependency, append it to `requirements.in`, install `pip-tools`
inside the virtual environment
and run `pip-compile requirements.in`.
See [pip-tools documentation](https://github.com/jazzband/pip-tools)
for details.

## App structure

* `tutti`: project module, for project-wide settings.
* `members`: membership management app, stores people, groups and the rest.
  Also includes a custom admin site for branding.
* `pages`: homepage and base template.
* `ldapsync`: synchronization of the members data with an LDAP server.
* `aadsync`: synchronization of the member accounts and groups to Azure Active Directory.
* `oidc`: handle user login via OpenID Connect.
