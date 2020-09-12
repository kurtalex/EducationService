from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login
from django.views.generic.edit import FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView

from .forms import CourseEnrollForm
from courses.models import Course


class StudentRegistrationView(CreateView):
    """
    template_name – имя HTML-шаблона, который будет использоваться;
    form_class – класс формы для создания объекта. Указанный класс должен быть наследником ModelForm.
     Мы указали форму UserCreationForm для создания объектов модели User;
    success_url – адрес, на который пользователь будет перенаправлен после успешной обработки формы регистрации.
     Мы получаем URL по имени student_course_list

    Метод form_valid() обработчика будет выполняться при успешной валидации формы.
    Он должен возвращать объект HTTP-ответа. Этот метод переопределен для того,
    чтобы после регистрации автоматически авторизовать пользователя на сайте.
    """
    template_name = 'students/student/registration.html'
    form_class = UserCreationForm
    success_url = reverse_lazy('student_course_list')

    def form_valid(self, form):
        result = super(StudentRegistrationView, self).form_valid(form)
        cd = form.cleaned_data
        user = authenticate(username=cd['username'],
                            password=cd['password'])

        login(self.request, user)

        return result


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    """
    Этот обработчик занимается зачислением студентов на курсы. Указав родительский класс
    LoginRequiredMixin, поэтому только авторизованные пользователи смогут записываться
    Также родительским классом является базовый обработчик Django, FormView, который реализует
    работу с формой.
    В атрибуте form_class указана форма CourseEnrollForm, которая при успешной валидации
    будет создавать связь между студентом и курсом
    Метод get_success_url() возвращает адрес, на который пользователь будет перенаправлен
    после успешной обработки формы.
    """
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super(StudentEnrollCourseView, self).form_valid(form)

    def get_success_url(self):
        return reverse_lazy('student_course_detail', args=[self.course.id])


class StudentCourseListView(LoginRequiredMixin, ListView):
    """
    Обработчик формирует список курсов, на которые зарегистрировался клиент.используем примесь LoginRequiredMixin,
    чтобы только авторизованные пользователи могли иметь доступ к этой странице.
    Этот обработчик также наследуется от класса ListView, чтобы отображать объекты модели
    Course в виде списка. Чтобы получить только курсы, связанные с текущим пользователем,
    мы переопределили метод get_queryset() и отфильтровали QuerySet курсов по связи ManyToManyField со студентом.
    """
    model = Course
    template_name = 'students/course/list.html'

    def get_queryset(self):
        qs = super(StudentCourseListView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentCourseDetailView(DetailView):
    """
    Обработчик StudentCourseDetailView. Переопределён метод get_queryset(),
    чтобы ограничить QuerySet курсов и работать только с теми, на которые записан текущий пользователь.
    метод get_context_data(), чтобы добавить в контекст шаблона данные о модуле, если его
    идентификатор был передан в параметре module_id URLʼа. В противном случае мы показываем
    содержимое первого модуля. Так студенты смогут переходить от одного модуля курса к другому.
    """
    model = Course
    template_name = 'students/course/detail.html'

    def get_queryset(self):
        qs = super(StudentCourseDetailView, self).get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super(StudentCourseDetailView, self).get_context_data(**kwargs)
        # Получаем объект курса
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # Получаем текущий модуль по параметрам запроса.
            context['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            # Получаем первый модуль.
            context['module'] = course.modules.all()[0]

        return context
