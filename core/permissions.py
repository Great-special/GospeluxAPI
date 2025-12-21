from rest_framework.permissions import BasePermission

class AllowOptionsPermission(BasePermission):
    def has_permission(self, request, view):
        if request.method == "OPTIONS":
            return True
        return True


