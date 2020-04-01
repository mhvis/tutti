from django.apps import AppConfig


class MembersConfig(AppConfig):
    name = 'members'

    def ready(self):
        # noinspection PyUnresolvedReferences
        import members.signals  # noqa: F401
