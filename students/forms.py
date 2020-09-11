from django import forms
from courses.models import Course


class CourseEnrollForm(forms.Form):
    """
    Форма для записи студентов на курсы. В поле course будет содержаться идентификатор курса
    на который происходтит запись. Тип выбран ModelChoiceField и виджет HiddenInput
    т.к. не хотим чтобы пользователь видел поле. Эта форма будет использоваться в обработчике
    CourseDetailView
    """
    course = forms.ModelChoiceField(queryset=Course.objects.all(), widget=forms.HiddenInput)

