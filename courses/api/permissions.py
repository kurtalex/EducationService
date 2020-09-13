from rest_framework.permissions import BasePermission


class IsEnrolled(BasePermission):
    """
    Проверяет, является ли текущий пользователь слушателем курса, через атрибут students
    объекта модели Course.
    """
    def has_object_permission(self, request, view, obj):
        return obj.students.filter(id=request.user.id).exists()



