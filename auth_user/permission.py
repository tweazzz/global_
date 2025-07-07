from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied

class IsAdminOrAccountant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['admin', 'accountant']

class IsAdminOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class CanOnlyAccountantUpdateIsPaid(permissions.BasePermission):
    message = 'Access denied: insufficient privileges.'

    def has_permission(self, request, view):
        # Все роли могут безопасные методы
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated

        # Только аутентифицированные пользователи могут делать небезопасные запросы
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        user = request.user
        method = request.method
        updated_fields = set(request.data.keys())

        if method in permissions.SAFE_METHODS:
            return True

        if user.role == 'admin':
            if 'is_paid' in updated_fields:
                raise PermissionDenied('Admins cannot modify is_paid.')
            return True

        if user.role == 'accountant':
            if method in ['PUT', 'PATCH']:
                if updated_fields.issubset({'is_paid'}):
                    return True
                raise PermissionDenied('Accountants can only modify is_paid.')
            if method in ['DELETE', 'POST']:
                raise PermissionDenied('Accountants cannot delete or create.')
            return False

        if user.role == 'employee':
            if obj.executor != user:
                raise PermissionDenied('Employees can only modify or delete their own records.')
            if 'is_paid' in updated_fields:
                raise PermissionDenied('Employees cannot modify is_paid.')
            return method in ['PUT', 'PATCH', 'DELETE']

        return False


class IsAdminRoleOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user and request.user.is_authenticated
        return request.user.is_authenticated and request.user.role == 'admin'