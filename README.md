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

* To create an admin user run `python manage.py createsuperuser`. You can bypass
  the OpenID Connect login flow by going to `http://127.0.0.1:8000/admin/login/`.
* To load sample data run `python manage.py loaddata sampledata`.
* For LDAP cloning and sync, see `python manage.py ldapclone -h` and `python
  manage.py ldapsync -h` for details.

## Development commands

Assumes that the environment is set correctly using `pipenv shell`.
Alternatively use `pipenv run <command>`.

* Run test server: `python manage.py runserver`
* Run unit tests: `python manage.py test`
* Lint code: `flake8`


## App structure

* `tutti`: project module, for project-wide settings.
* `members`: membership management app, stores people, groups and the rest.
  Also includes a custom admin site for branding.
* `pages`: homepage and base template.
* `ldapsync`: synchronization of the members data with an LDAP server.
* `aadsync`: synchronization of the member accounts and groups to Azure Active Directory.
* `oidc`: handle user login via OpenID Connect.
