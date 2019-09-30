# ldapproxy

This app makes the member database available for use by OpenLDAP to present it
using the LDAP protocol.

## Setup

* Install OpenLDAP and an ODBC driver for the used database (likely PostgreSQL)
* Add record to `odbc.ini` file
* Configure OpenLDAP using `ldif` files
  * `ldapadd` / `ldapmodify`



## LDIF

```
#######################################################################
# sql database definitions
#######################################################################

database	sql
suffix		"o=sql,c=RU"
rootdn		"cn=root,o=sql,c=RU"
rootpw		secret
dbname		PostgreSQL
dbuser		postgres
dbpasswd	postgres
insentry_stmt	"insert into ldap_entries (id,dn,oc_map_id,parent,keyval) values ((select max(id)+1 from ldap_entries),?,?,?,?)"
upper_func	"upper"
strcast_func	"text"
concat_pattern	"?||?"
has_ldapinfo_dn_ru	no
```