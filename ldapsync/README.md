# ldapsync

Keeps data in sync with LDAP server.





## Changelog

### v1

One-way sync to LDAP.


## Implementation notes

* Changes in Django are propagated to LDAP instantly via Django save/delete
signals. Changes that are missed due to not having had signals sent can be
propagated using a sync command.
* An entry in LDAP is matched to the corresponding entry in Django using an
LDAP attribute which stores the primary key of the Django entry.
* A copy of the data in LDAP is stored locally in order to find out if entries
in LDAP have changed. If that is the case, any operation is blocked. The
changes in LDAP are not automatically synced to Django, only the other way
around. This would thus require manual intervention to fix.
