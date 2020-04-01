# Deployment

[Ansible](https://docs.ansible.com/ansible/latest/index.html) Playbook for
deployment to an Azure virtual machine.

Deployment configuration for backup is not included here, but kept in
https://github.com/mhvis/doqumentatie.

## Instructions

1. Prepare virtual machine:
    1. Create Azure virtual machine with Ubuntu 18.04 LTS, accessible using an SSH key.
    2. Create an Azure Key Vault for storing secrets.
    3. Set up Managed Service Identity for the virtual machine, so that it can access the key vault.
       ([more info](https://docs.microsoft.com/en-us/azure/key-vault/tutorial-python-linux-virtual-machine))
2. Put secrets inside the key vault, see `roles/web/templates/azuresettings.py.j2` for the necessary secrets.
3. Check/modify variables in:
    * `vars.yml`
    * `roles/web/templates/azuresettings.py.j2`
4. Play deployment config:
    1. Install Ansible on your local machine.
    2. Put the remote Azure virtual machine(s) in the `hosts` file.
    3. Run `ansible-playbook -i hosts site.yml`.

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
