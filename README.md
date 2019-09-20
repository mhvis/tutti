# QLUIS

```
Quadrivium
Leden
U..?
I..?
Systeem
```

Naam kan beter

## Installation

Make sure that Pipenv is installed. Run the following commands:

* `pipenv install --dev`
* `pipenv shell`
* `python manage.py migrate`
* `python manage.py createsuperuser`

For deployments, it's easiest to add a `.env` file to specify a custom Django
settings module. Pipenv will automatically set the environment variables in
that file.

## Development commands

Assumes that the environment is set correctly using `pipenv shell`.
Alternatively use `pipenv run`.

* Run test server: `python manage.py runserver`
* Run unit tests: `python manage.py test`
* Lint code: `flake8`
