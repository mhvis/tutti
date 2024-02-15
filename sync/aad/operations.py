from abc import ABCMeta
from typing import Dict

from django.conf import settings

from sync.aad.graph import GraphUser, GraphGroup, Graph


class SyncOperation:
    """Operation to be applied in Azure Active Directory."""

    def __str__(self) -> str:
        return repr(self)

    def apply(self, graph: Graph):
        raise NotImplementedError


class CreateUserOperation(SyncOperation):
    """Create a new user.

    Also adds a license for the user.
    """

    def __init__(self, user: GraphUser):
        self.user = user

    def apply(self, graph: Graph):
        """Creates the user with extension data and assigns the license."""
        # Create user
        user_id = graph.create_user(self.user)
        # Add extension data (Tutti database ID)
        graph.add_user_extension(user_id, self.user.extension)
        if settings.GRAPH_LICENSE_SKU_ID:
            # Assign Microsoft 365 license
            graph.assign_license(user_id=user_id, sku_id=settings.GRAPH_LICENSE_SKU_ID)

    def __repr__(self):
        return "CreateUser({})".format(repr(self.user))


class DeleteUserOperation(SyncOperation):
    def __init__(self, user: GraphUser):
        self.user = user

    def __repr__(self) -> str:
        return "DeleteUser({})".format(self.user.user_principal_name)

    def apply(self, graph: Graph):
        graph.delete_user(self.user.directory_id)


class UpdateUserOperation(SyncOperation):
    def __init__(self, user: GraphUser, changes: Dict):
        self.user = user
        self.changes = changes

    def __repr__(self) -> str:
        return "UpdateUser({}, {})".format(self.user.user_principal_name, repr(self.changes))

    def apply(self, graph: Graph):
        graph.update_user(self.user.directory_id, self.changes)


class CreateGroupOperation(SyncOperation):
    def __init__(self, group: GraphGroup):
        self.group = group

    def __repr__(self) -> str:
        return "CreateGroup({})".format(repr(self.group))

    def apply(self, graph: Graph):
        group_id = graph.create_group(self.group)
        graph.add_group_extension(group_id, self.group.extension)


class DeleteGroupOperation(SyncOperation):
    def __init__(self, group: GraphGroup) -> None:
        self.group = group

    def apply(self, graph: Graph):
        graph.delete_group(self.group.directory_id)

    def __repr__(self) -> str:
        return "DeleteGroup({})".format(self.group.display_name)


class UpdateGroupOperation(SyncOperation):
    def __init__(self, group: GraphGroup, changes: Dict) -> None:
        self.group = group
        self.changes = changes

    def apply(self, graph: Graph):
        graph.update_group(self.group.directory_id, self.changes)

    def __repr__(self) -> str:
        return "UpdateGroup({}, {})".format(self.group.display_name, self.changes)


class BaseGroupMemberOperation(SyncOperation, metaclass=ABCMeta):
    def __init__(self, group: GraphGroup, user: GraphUser):
        self.group = group
        self.user = user


class AddGroupMemberOperation(BaseGroupMemberOperation):
    def __repr__(self) -> str:
        return "AddGroupMember({}, {})".format(self.group.display_name, self.user.user_principal_name)

    def apply(self, graph: Graph):
        graph.add_group_member(self.group.directory_id, self.user.directory_id)


class RemoveGroupMemberOperation(BaseGroupMemberOperation):
    def __repr__(self) -> str:
        return "RemoveGroupMember({}, {})".format(self.group.display_name, self.user.user_principal_name)

    def apply(self, graph: Graph):
        graph.remove_group_member(self.group.directory_id, self.user.directory_id)
