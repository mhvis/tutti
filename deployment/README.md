# Deployment

[Ansible](https://docs.ansible.com/ansible/latest/index.html) Playbook for
deployment to a virtual machine.

Deployment configuration for backup is not included here, but kept in
https://github.com/mhvis/doqumentatie.

## Requirements

* Ubuntu 18.04 LTS machine to deploy to
* Azure Key Vault for secret storage, see `roles/web/templates/azuresettings.py.j2` for the necessary secrets
* To run the deployment, you'll need to have installed locally, so not on the remote server:
  * Ansible
  * AzureCLI, for retrieving the secrets in Azure Key Vault.
    After installation, run `az login` to log in with Q account.

## Usage

1. Check/modify variables in:
    * `vars.yml`
    * `roles/web/templates/azuresettings.py.j2`
    * `hosts` (stores the hostname for the deployment over SSH)
2. Run `ansible-playbook -i hosts site.yml`

## Other playbooks/tags

* `ansible-playbook -i hosts reset.yml`: this removes the database, uploaded files,
  randomly generated secrets.
* `ansible-playbook -i hosts site.yml --tags "app"`: this does a quick update
  on an already deployed host by skipping installation steps and only updating
  source code.

## Todo

(Not very important)

* Remove the roles and use includes instead to make the structure simpler.
* Remove Microsoft Identity Manager code from `azuresettings.py`, use client-side secret retrieval.


## Resources

The playbook is based on https://github.com/jcalazan/ansible-django-stack
