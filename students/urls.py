from django.urls import path, include
from . import views

urlpatterns = [path('register/', views.StudentRegistrationView.as_view(), name='student_registration'),

               ]
