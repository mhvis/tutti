# Sync

Package layout:

* Modules `clone.py`, `ldap*.py` and `sync.py` all deal with LDAP synchronization.
* Package `aad` deals with Azure Active Directory synchronization.
* Module `signals.py` sets up the tasks that run the synchronizations periodically and on save.
* There are a couple of management commands that will run synchronization manually.
    They are not meant for use with cron.

## Random AAD notes

* > Federated users created using this API will be forced to sign-in every 12 hours by default. For more information on
how to change this, see [Exceptions for token lifetimes](https://docs.microsoft.com/azure/active-directory/develop/active-directory-configurable-token-lifetimes#exceptions).
* Users need to have a license assigned after creation to use SharePoint (this is implemented).
* Full API reference: https://docs.microsoft.com/en-us/graph/api/overview?view=graph-rest-1.0
