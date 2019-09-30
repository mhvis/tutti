"""Database tables in the format for OpenLDAP.

See servers/slapd/back-sql/rdbms_depend/pgsql in the OpenLDAP source code for
the details.
"""

from django.db import models


class ObjectClassMapping(models.Model):
    """Mapping between object class and primary key database table."""

    class Meta:
        db_table = 'ldap_oc_mappings'

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=64)
    key_table = models.CharField(max_length=64, db_column='keytbl')
    key_column = models.CharField(max_length=64, db_column='keycol')
    # create_proc = models.CharField(max_length=255, null=True)
    # delete_proc = models.CharField(max_length=255, null=True)
    # expect_return = models.IntegerField()


class AttributeMapping(models.Model):
    """Mapping between LDAP attributes and corresponding SQL queries."""

    class Meta:
        db_table = 'ldap_attr_mappings'

    id = models.AutoField(primary_key=True)
    object_class_mapping = models.ForeignKey(ObjectClassMapping,
                                             on_delete=models.CASCADE,
                                             db_column='oc_map_id')
    name = models.CharField(max_length=255)
    select_expression = models.CharField(max_length=255, db_column='sel_expr')
    from_tables = models.CharField(max_length=255, db_column='from_tbls')
    join_where = models.CharField(max_length=255, null=True)


class LdapEntry(models.Model):
    class Meta:
        db_table = 'ldap_entries'

    id = models.AutoField(primary_key=True)
    dn = models.CharField(max_length=255)
    object_class_mapping = models.ForeignKey(ObjectClassMapping,
                                             on_delete=models.CASCADE,
                                             db_column='oc_map_id')
    parent = models.ForeignKey('self', on_delete=models.PROTECT, null=True)
    key_value = models.IntegerField(db_column='keyval')
    """References the primary key of the entry in the corresponding table."""


class LdapEntryObjectClasses(models.Model):
    class Meta:
        db_table = 'ldap_entry_objclasses'

    entry_id = models.OneToOneField(LdapEntry,
                                    on_delete=models.CASCADE,
                                    db_column='entry_id',
                                    primary_key=True)
    object_class_name = models.CharField(max_length=64, db_column='oc_name')
