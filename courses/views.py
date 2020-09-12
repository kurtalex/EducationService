from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect, get_object_or_404
from django.views.generic.base import TemplateResponseMixin, View
from django.forms.models import modelform_factory
from django.apps import apps
from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.db.models import Count
from django.views.generic.detail import DetailView
from django.core.cache import cache

from .models import Module, Content
from .forms import ModuleFormSet
from .models import Course
from .models import Subject
from students.forms import CourseEnrollForm

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


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin):
    model = Course
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    fields = ['subject', 'title', 'slug', 'overview']
    success_url = reverse_lazy('manage_course_list')
    template_name = 'courses/manage/course/form.html'


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = 'courses/manage/course/list.html'


class CourseCreateView(PermissionRequiredMixin, OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'


class CourseUpdateView(PermissionRequiredMixin, OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


class CourseDeleteView(PermissionRequiredMixin, OwnerCourseMixin, DeleteView):
    template_name = 'courses/manage/course/delete.html'
    success_url = reverse_lazy('manage_course_list')
    permission_required = 'courses.delete_course'


"""
Класс CourseModuleUpdateView обрабатывает действия, связанные с набором
форм по сохранению, редактированию и удалению модулей для конкретного
курса.
"""


class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSet(instance=self.course, data=data)

    def dispatch(self, request, pk):
        self.course = get_object_or_404(Course,
                                        id=pk,
                                        owner=request.user)
        return super(CourseModuleUpdateView, self).dispatch(request, pk)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course, 'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()
            return redirect('manage_course_list')
        return self.render_to_response({'course': self.course,
                                        'formset': formset})


"""
ContentCreateUpdateView - позволит создавать и редактировать содержимое различных типов
get_model() – возвращает класс модели по переданному имени. Допусти-
мые значения – Text, Video, Image и File
get_form() – создает форму в зависимости от типа содержимого с помощью
функции modelform_factory().
dispatch() – получает приведенные ниже данные из запроса и создает
соответствующие объекты модуля, модели содержимого
get() – извлекает из GET-параметров запроса данные. Формирует модель-
ные формы для объектов Text, Video, Image или File, если объект редакти-
руется, т. е. указан self.obj. В противном случае мы отображаем пустую
форму для создания объекта;
post() – обрабатывает данные POST-запроса, для чего создает модель-
ную форму и валидирует ее. Если форма заполнена корректно, создает
новый объект, указав текущего пользователя, request.user, владельцем.
Если в запросе был передан ID, значит, объект изменяют, а не создают.
"""


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None

    template_name = 'courses/manage/content/form.html'

    def get_model(self, model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)

        return None

    def get_form(self, model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner',
                                                 'order',
                                                 'created',
                                                 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module,
                                        id=module_id,
                                        course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model,
                                         id=id,
                                         owner=request.user)
        return super(ContentCreateUpdateView,
                     self).dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form, 'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model,
                             instance=self.obj,
                             data=request.POST,
                             files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # Создаем новый объект.
                Content.objects.create(module=self.module, item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({'form': form, 'object': self.obj})


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Course,
                                    id=id,
                                    module__course__owner=request.user)
        module = content.module
        content.item.delete()
        content.delete()
        return redirect('module_content_list', module.id)


"""
ModuleContentListView - получает из базы данных модуль по
переданному ID и генерирует для него страницу подробностей.
"""


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module,
                                   id=module_id,
                                   course__owner=request.user)
        return self.render_to_response({'module': module})


"""
ModuleOrderView - обработчик, который получает новый порядок модулей в формате JSON

"""


class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def pos(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id,
                                  course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id,
                                   module__course__owner=request.user).update(order=order)

        return self.render_json_response({'saved': 'OK'})


"""Отображение курсов для студентов"""


class CourseListView(TemplateResponseMixin, View):
    """
    При обработке запроса на получение курсов мы выполняем следующие действия:
    1) получаем список всех предметов, добавляя количество курсов по каждому из них.
     Для этого применяем метод annotate() QuerySetʼа и функцию агрегации Count();
    2) получаем все доступные курсы, включая количество модулей для каждого из них;
    3) если в URLʼе задан слаг предмета, получаем объект предмета и фильтруем список курсов по нему;
    4) для формирования результата используем метод render_to_response() из примеси TemplateResponseMixin.
    """
    model = Course
    template_name = 'courses/course/list.html'

    def get(self, request, subject=None):
        # subjects = Subject.objects.annotate(total_courses=Count('courses'))
        """
        Добавлена возможность кэширования страницы(курсов), если кеша нет, то страница сначала кэшируется
        а потом из кэша отрисовывается у пользователя
        :param request:
        :param subject:
        :return:
        """
        subjects = cache.get('all_subjects')
        if not subjects:
            subjects = Subject.objects.annotate(total_courses=Count('courses'))
            cache.set('all_subjects', subjects)
        all_courses = Course.objects.annotate(total_modules=Count('modules'))

        # courses = Course.objects.annotate(total_modules=Count('modules'))
        if subject:
            # subject = get_object_or_404(Subject, slug=subject)
            # courses = courses.filter(subject=subject)
            subject = get_object_or_404(Subject, slug=subject)
            key = 'subject_{}_courses'.format(subject.id)
            courses = cache.get(key)
            if not courses:
                courses = all_courses.filter(subject=subject)
                cache.set(key, courses)
        else:
            courses = cache.get('all_courses')
            if not courses:
                courses = all_courses
                cache.set('all_courses', courses)

        return self.render_to_response({'subjects': subjects,
                                        'subject': subject,
                                        'courses': courses})


class CourseDetailView(DetailView):
    """
    Указаны два атрибута: model и template_name. При обработке запроса Django ожидает,
    что в URL будет передан идентификатор (pk) объекта, по которому его можно получить
    Затем формирует результат в виде HTML-страницы, сгенерированной из шаблона с именем
    template_name. В контекст шаблона добавляется переменная - объект модели.

    переопределяем метод базового класса get_context_data(), чтобы добавить форму
    в контекст шаблона. Объект формы при этом содержит скрытое поле с ID курса, поэтому
    при нажатии кнопки на сервер будут отправлены данные курса и пользователя.

     """
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs):
        context = super(CourseDetailView, self).get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(initial={'course': self.object})

        return context
