from django.db import models
from django.contrib.auth.models import User

"""
owner - пользователь, который создал курс
subjects - предмет, к которому привязан курс. Это внешний ForeignKey на модель Subject
title - название курса
slug - слаг курса, будет использоваться для формирования понятных URL'ов
overview - текстовое поле для создания краткого описания курса
created - дата и время создания курса ПРОСТАВЛЯЮТСЯ АВТОМАТИЧЕСКИ
"""

class Subject(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)  # “Slug” – это короткое название-метка, которое содержит

    # только буквы, числа, подчеркивание или дефис. В основном используются в URL.

    class Meta:
        ordering = ['title']

    def __str__(self):
        return self.title


class Course(models.Model):
    owner = models.ForeignKey(User, related_name='courses_created', on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, related_name='courses', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    overview = models.TextField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return self.title


class Module(models.Model):
    course = models.ForeignKey(Course, related_name='modules', on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.title
