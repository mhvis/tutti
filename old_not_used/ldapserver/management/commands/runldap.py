import sys
from argparse import ArgumentParser

from django.core.management import BaseCommand
from ldaptor import inmemory
from ldaptor.interfaces import IConnectedLDAPEntry
from ldaptor.protocols import pureldap
from ldaptor.protocols.ldap import ldapserver, ldaperrors
from twisted.internet import reactor, protocol
from twisted.python import components
from twisted.python import log

from ldapserver import schema
from qluis.models import Person


class Command(BaseCommand):
    help = 'Run the LDAP server'

    def add_arguments(self, parser: ArgumentParser):
        pass

    def construct_db(self):
        db = inmemory.ReadOnlyInMemoryLDAPEntry('', {})
        db.addChild('cn=schema',
                    {'objectClass': schema.OBJECT_CLASS,
                     'cn': ['schema'],
                     'objectClasses': schema.OBJECT_CLASSES,
                     'attributeTypes': schema.ATTRIBUTE_TYPES,
                     'matchingRules': schema.MATCHING_RULES,
                     'ldapSyntaxes': schema.LDAP_SYNTAXES,
                     })
        nl = db.addChild('dc=nl',
                         {'objectClass': ['top', 'dcObject'],
                          'dc': ['nl'],
                          })
        org_root = nl.addChild('dc=esmgquadrivium',
                               {'objectClass': ['top', 'dcObject'],
                                'dc': ['esmgquadrivium'],
                                })
        people = org_root.addChild('ou=People', {
            'objectClass': ['organizationalUnit', 'top'],
            'ou': ['People'],
        })
        groups = org_root.addChild('ou=Groups', {
            'objectClass': ['organizationalUnit', 'top'],
            'ou': ['Groups'],
        })
        for p in Person.objects.all():
            people.addChild('uid={}'.format(p.username), {
                'objectClass': ['person', 'top', 'uidObject'],
                'sn': [p.last_name],
                'cn': [p.get_full_name()],
                'uid': [p.username],

            })
        return db

    def handle(self, *args, **options):
        log.startLogging(sys.stderr)

        class LDAPServerFactory(protocol.ServerFactory):
            def __init__(self, root):
                self.root = root

        class MyLDAPServer(ldapserver.LDAPServer):
            debug = True

            def getRootDSE(self, request, reply):
                root = IConnectedLDAPEntry(self.factory)
                reply(pureldap.LDAPSearchResultEntry(
                    objectName='',
                    attributes=[
                        ('objectClass', ['top']),
                        ('supportedLDAPVersion', ['3']),
                        ('namingContexts', ['dc=esmgquadrivium,dc=nl']),
                        ('supportedExtension', [
                            pureldap.LDAPPasswordModifyRequest.oid, ]),
                        ('subschemaSubentry', ['cn=schema'])
                    ], ))
                return pureldap.LDAPSearchResultDone(
                    resultCode=ldaperrors.Success.resultCode)

        components.registerAdapter(lambda x: x.root,
                                   LDAPServerFactory,
                                   IConnectedLDAPEntry)

        db = self.construct_db()
        factory = LDAPServerFactory(db)
        factory.protocol = MyLDAPServer
        reactor.listenTCP(10389, factory)
        reactor.run()
