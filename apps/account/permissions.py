# from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS
from SLIMS.envs import common as settings


def PermissionSeperator(str):
    list = str.split('_')
    return list[0], list[1], list[2]

def query_set_filter_key(view_key, user_access_levels, required_access_levels, requrest_method):
    if required_access_levels is None:
        return 'all'
    user_access_levels = user_access_levels.values_list('access_key', flat=True)
    methods = {"GET": "view", "POST": "create", "PUT": "update", "PATCH": "update", "DELETE": "delete"}

    required_access_levels_filter = [access_level for access_level in required_access_levels if
                                   access_level.startswith(methods[requrest_method])]
    user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if
                                 user_access_level.split('_')[2] == view_key and user_access_level.startswith(methods[requrest_method])]

    user_access_levels_filter_list = list(user_access_levels_filter)
    required_access_levels_filter_list = list(required_access_levels_filter)
    if any(level in user_access_levels_filter_list for level in required_access_levels_filter_list):
        query_filters = [x.split('_')[1] for x in list(user_access_levels_filter_list)]
        if 'all' in query_filters:
            return 'all'
        elif 'owner' in query_filters:
            return 'owner'
        # if 'receptor' in query_filters:
        #     return 'receptor'
        # elif 'operator' in query_filters:
        #     return 'operator'
        # if 'receptor' in query_filters:
        #     return 'all'
        # elif 'operator' in query_filters:
        #     return 'owner'

    return None  # all or owner


class AccessLevelPermission(BasePermission):
    """
    Custom permission to allow access based on user's access levels.
    """

    def has_permission(self, request, view):
        required_access_levels = getattr(view, 'required_access_levels', None)
        view_key = getattr(view, 'view_key', None)

        if required_access_levels is None:
            return True
        if not request.user.is_authenticated:
            return False
        user_access_levels = request.user.get_access_levels().values_list('access_key', flat=True)

        if request.method in ['GET']:
            required_view_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('view')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]
            return any(level in user_access_levels_filter for level in required_view_access_levels)

        if request.method in ['POST']:
            required_create_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('create')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]
            return any(level in user_access_levels_filter for level in required_create_access_levels)

        if request.method in ['PUT', 'PATCH']:
            required_update_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('update')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]
            return any(level in user_access_levels_filter for level in required_update_access_levels)

        if request.method in ['DELETE']:
            required_delete_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('delete')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]
            return any(level in user_access_levels_filter for level in required_delete_access_levels)

    def has_object_permission(self, request, view, obj):
        required_access_levels = getattr(view, 'required_access_levels', None)
        view_key = getattr(view, 'view_key', None)

        if required_access_levels is None:
            return True
        if not request.user.is_authenticated:
            return False
        user_access_levels = request.user.get_access_levels().values_list('access_key', flat=True)
        filter_key = query_set_filter_key(view.view_key, view.request.user.get_access_levels(), view.required_access_levels, view.request.method)

        if request.method in ['GET']:
            required_view_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('view')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]

            if filter_key == 'all' or filter_key == 'receptor':
                return any(level in user_access_levels_filter for level in required_view_access_levels)
            elif filter_key == 'owner' or filter_key == 'operator':
                return request.user in obj.owners() and any(level in user_access_levels_filter for level in required_view_access_levels)

        if request.method in ['POST']:
            required_create_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('create')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]

            if filter_key == 'all' or filter_key == 'receptor':
                return any(level in user_access_levels_filter for level in required_create_access_levels)
            elif filter_key == 'owner' or filter_key == 'operator':
                return request.user in obj.owners() and any(level in user_access_levels_filter for level in required_create_access_levels)

        if request.method in ['PUT', 'PATCH']:
            required_update_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('update')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]

            if filter_key == 'all' or filter_key == 'receptor':
                return any(level in user_access_levels_filter for level in required_update_access_levels)
            elif filter_key == 'owner' or filter_key == 'operator':
                return request.user in obj.owners() and any(
                    level in user_access_levels_filter for level in required_update_access_levels)

        if request.method in ['DELETE']:
            required_delete_access_levels = [access_level for access_level in required_access_levels if access_level.startswith('delete')]
            user_access_levels_filter = [user_access_level for user_access_level in user_access_levels if user_access_level.split('_')[2] == view_key]

            if filter_key == 'all' or filter_key == 'receptor':
                return any(level in user_access_levels_filter for level in required_delete_access_levels)
            elif filter_key == 'owner' or filter_key == 'operator':
                return request.user in obj.owners() and any(
                    level in user_access_levels_filter for level in required_delete_access_levels)


class Authenticated(BasePermission):
    """
    Allows access only to registered users.
    """

    def has_permission(self, request, view):
        return is_authenticated(request.user)


class IsOwnerOrReadOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
        return obj.owner == request.user


class IsOwnerProfile(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
        return obj.profile == request.user.profile or obj.receiver == request.user.profile

class IsOwnerProfileOnly(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
        return obj.profile == request.user.profile


class IsProfileSubclassOwner(BasePermission):
    """
    Object-level permission to only allow owners of an object to edit it.
    Assumes the model instance has an `owner` attribute.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        # if request.method in permissions.SAFE_METHODS:
        #     return True

        # Instance must have an attribute named `owner`.
        return obj.profile.user == request.user


class IsSuperuserOrStaff(BasePermission):
    """
    Allows access only to superusers, staff members, and object owners.
    """

    def has_permission(self, request, view):
        # Check access for non-GET requests
        if request.user.is_superuser or request.user.is_staff:
            return True
        return False


class IsSuperuserOrStaffOrOwner(BasePermission):
    """
    Allows access only to superusers, staff members, and object owners.
    """

    def has_permission(self, request, view):
        # Check access for non-GET requests
        if request.method != 'GET':
            # Allow access for superusers and object owners
            if request.user.is_superuser or request.user.is_staff or request.user == view.get_object():
                return True
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # Check access for GET requests
        # Allow access for superusers and object owners
        if request.method == 'GET':
            if request.user.is_superuser or request.user.is_staff or request.user == obj:
                return True
        return False


class IsSelfOrManager(BasePermission):
    """
    Custom permission to only allow managers and profile owners to take action.
    """

    def has_object_permission(self, request, view, obj):
        if settings.IGNORE_PERMISSIONS:
            return settings.IGNORE_PERMISSIONS
        # Write permissions are only allowed to the owner of the snippet.
        return request.user and (obj.user.username == request.user.username or is_in_group(request.user, 'manager') or is_in_group(request.user, 'expert'))


class IsExpertOrAdminOrManager(BasePermission):
    """
    Custom permission to only allow managers and profile owners to take action.
    """
    def has_permission(self, request, view):
        return request.user and (is_in_group(request.user, ['manager', 'expert', 'admin']))

    def has_object_permission(self, request, view, obj):
        if settings.IGNORE_PERMISSIONS:
            return settings.IGNORE_PERMISSIONS
        # Write permissions are only allowed to the owner of the snippet.
        return request.user and (is_in_group(request.user, ['manager', 'expert', 'admin']))


class IsAdminOrManager(BasePermission):
    """
    Custom permission to only allow managers and profile owners to take action.
    """
    def has_permission(self, request, view):
        return request.user and (is_in_group(request.user, ['manager', 'admin']))

    def has_object_permission(self, request, view, obj):
        if settings.IGNORE_PERMISSIONS:
            return settings.IGNORE_PERMISSIONS
        # Write permissions are only allowed to the owner of the snippet.
        return request.user and (is_in_group(request.user, ['manager', 'admin']))


class IsAdminOrManagerOrReadOnly(BasePermission):
    """
    Custom permission to only allow managers and profile owners to take action.
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return request.user and (is_in_group(request.user, ['manager', 'expert', 'admin']))

    def has_object_permission(self, request, view, obj):
        if settings.IGNORE_PERMISSIONS:
            return settings.IGNORE_PERMISSIONS
        if request.method in SAFE_METHODS:
            return True
        # Write permissions are only allowed to the owner of the snippet.
        return request.user and (is_in_group(request.user, ['manager', 'expert', 'admin']))


def is_authenticated(user):
    # return (user and user.is_active) or settings.IGNORE_PERMISSIONS
    return (user and user.is_active)


def is_in_group(user, group_name):
    if type(group_name) not in [tuple, list]:
        group_name = [group_name]
    return (user and user.groups.filter(name__in=group_name).count() > 0) or settings.IGNORE_PERMISSIONS

