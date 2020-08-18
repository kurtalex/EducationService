from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from .models import Course


# class ManageCourseListView(ListView):
#     model = Course
#     template_name = 'courses/manage/course/list.html'
#
#     def get_queryset(self):
#         qs = super(ManageCourseListView, self).get_queryset()
#         return qs.filter(owner=self.request.user)

"""
В этом фрагменте определяются две примеси: OwnerMixin и OwnerEditMixin.
Они будут добавлены к обработчикам вместе с такими классами Django,
как ListView, CreateView, UpdateView и DeleteView. Примесь OwnerMixin определяет
метод get_queryset(). Он используется для получения базового QuerySetʼа, с ко-
торым будет работать обработчик. Этот метод переотпределён, так чтобы
получать только объекты, владельцем которых является текущий пользователь
(request.user).
"""


class OwnerMixin(object):
    def get_queryset(self):
        qs = super(OwnerMixin, self).get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin(object):
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super(OwnerEditMixin, self).form_valid(form)


class OwnerCourseMixin(OwnerMixin):
    model = Course


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    pass


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    pass


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('manage_course_list')
