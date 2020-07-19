# Sync to Azure Active Directory

Responsibility: sync user accounts and groups with Azure Active Directory,
needed for SharePoint.

## PoC

Tested the following:

* Was able to create user with Graph API

## Resources

* User properties: https://docs.microsoft.com/en-us/graph/api/resources/user?view=graph-rest-1.0
  * onPremises{ImmutableId|LastSyncDateTime|SyncEnabled}. Most are read-only, except for ImmutableId.
  * usageLocation: must be set to NL for licensing.
* Create User API: https://docs.microsoft.com/en-us/graph/api/user-post-users?view=graph-rest-1.0&tabs=http
* Assign license: https://docs.microsoft.com/en-us/graph/api/user-assignlicense?view=graph-rest-1.0&tabs=http
  * Needed to enable O365 services for new accounts.

## Misc

> Federated users created using this API will be forced to sign-in every 12 hours by default. For more information on
how to change this, see [Exceptions for token lifetimes](https://docs.microsoft.com/azure/active-directory/develop/active-directory-configurable-token-lifetimes#exceptions).

## Federation

For Single-Sign On using Keycloak, see doQumentatie.