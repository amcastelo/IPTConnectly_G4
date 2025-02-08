from rest_framework.permissions import BasePermission


class IsPostAuthor(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.groups.filter(name='Admin').exists()
    
class IsPostAuthorOrAdmin(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        return obj.author == request.user or request.user.groups.filter(name="Admin").exists()