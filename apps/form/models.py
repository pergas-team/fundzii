from django.db import models

from apps.account.models import User


class Form(models.Model):
    title = models.CharField(max_length=100)
    json_init = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    owner = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="forms")

    def __str__(self):
        return self.title

    def owners(self):
        return [experiment.laboratory.technical_manager for experiment in self.experiments.all()] + [self.owner]

class Section(models.Model):
    title = models.CharField(max_length=100)
    form = models.ForeignKey(Form, related_name='sections', on_delete=models.CASCADE, verbose_name='فرم')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Field(models.Model):
    title = models.CharField(max_length=100)
    section = models.ForeignKey(Section, related_name='fields', on_delete=models.CASCADE, verbose_name='سطر')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title