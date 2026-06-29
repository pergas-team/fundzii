from rest_framework.exceptions import NotAuthenticated, PermissionDenied
from rest_framework.permissions import BasePermission


def is_admin_or_operator(user):
    return user.is_authenticated and (
        user.is_staff or user.groups.filter(name__iexact='operator').exists()
    )


class IsAuthenticatedJSON(BasePermission):
    """Return 401 (not 403) for unauthenticated requests."""

    def has_permission(self, request, view):
        if request.user and request.user.is_authenticated:
            return True
        raise NotAuthenticated(detail='برای انجام این عملیات باید وارد شوید.')


class IsAdminOrOperator(IsAuthenticatedJSON):
    def has_permission(self, request, view):
        super().has_permission(request, view)
        if is_admin_or_operator(request.user):
            return True
        raise PermissionDenied(detail='شما به این بخش دسترسی ندارید.')


class IsPartnerUser(IsAuthenticatedJSON):
    """Attach request.partner and request.partner_role when the user belongs to an active partner."""

    def has_permission(self, request, view):
        super().has_permission(request, view)
        membership = (
            request.user.partner_memberships
            .select_related('partner')
            .filter(partner__is_active=True)
            .first()
        )
        if not membership:
            raise PermissionDenied(detail='شما عضو هیچ همکار مالی فعالی نیستید.')
        request.partner = membership.partner
        request.partner_role = membership.role
        return True
