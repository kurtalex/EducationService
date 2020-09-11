from django.urls import reverse_lazy
from django.views.generic.edit import CreateView
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login


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
