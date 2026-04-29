from rest_framework.permissions import BasePermission
from .models import Company


class IsAdminUser(BasePermission):
    """Allow access only to TeamBoard platform admins stored in Company.role."""
    message = 'Only TeamBoard admin users can access this endpoint.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        try:
            return user.company.role == Company.Role.ADMIN
        except Company.DoesNotExist:
            return False
