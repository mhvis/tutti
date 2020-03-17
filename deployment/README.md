# Deployment

[Ansible](https://docs.ansible.com/ansible/latest/index.html) Playbook for
deployment to a remote machine. This is a complete deployment which includes (will include)
automatic backup creation.

To deploy:

1. Install Ansible on a local machine.
2. Put the remote machine(s) where this should be deployed in `hosts`.
    You'll need to have SSH keys setup.
3. Modify variables in `site.yml` if needed.
4. Run `ansible-playbook -i hosts site.yml`.


## Resources

The playbook is based on https://github.com/jcalazan/ansible-django-stack

Backups (todo): https://github.com/borgbase/ansible-role-borgbackup
or https://github.com/SphericalElephant/ansible-role-borgbackup
