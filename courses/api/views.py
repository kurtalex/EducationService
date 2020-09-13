from rest_framework import generics
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.authentication import BasicAuthentication
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from rest_framework.decorators import action

from ..models import Subject
from ..models import Course
from .serializers import SubjectSerializer
from .serializers import CourseSerializer


class SubjectListView(generics.ListAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


class SubjectDetailView(generics.RetrieveAPIView):
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer


# class CourseEnrollView(APIView):
#     """
#     Обработчик CourseEnrollView зачисляет студентов на курсы. порядок работы:
#     1. Метод post() для обработки POST-запросов. Другие методы не будут обрабатываться
#     2. Получение курса, на который происходит зачисление, обращаясь к POST-параметру
#     запроса pk. если курса не существует, то будет получено исключение с кодом 404
#     3. Если курс определён, создаём связь между студентом и объектом модели Course,
#     возвращая ответ с успешным статусом
#     """
#
#     authentication_classes = (BasicAuthentication,)
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request, pk, format=None):
#         course = get_object_or_404(Course, pk=pk)
#         course.students.add(request.user)
#         return Response({'enrolled': True})


class CourseViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Используем декоратор action(detail=True), чтобы показать, что метод работает с одним объектом,
    а не списком
    В качестве аргумента передаем в декоратор список HTTP-методов, с которыми может работать функция enroll(),
    а также классы для авторизации пользователей и проверки прав доступа;
    Вызываем метод self.get_object(), чтобы получить объект Course;
    Добавляем связь students текущего пользователя и курса, на который он пытается записаться.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    @action(detail=True, methods=['post'], authentication_classes=[BasicAuthentication],
            permission_classes=[IsAuthenticated])
    def enroll(self, request, *args, **kwargs):
        course = self.get_object()
        course.students.add(request.user)
        return Response({'enrolled': True})
