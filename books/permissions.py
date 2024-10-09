from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminAllOrReadOnly(BasePermission):
    """
    Allows read-only access to all users, but only admins (is_staff) can modify data.
    """

    def has_permission(self, request, view):
        return bool(
            (request.method in SAFE_METHODS) or (request.user and request.user.is_staff)
        )
