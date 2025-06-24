from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from .managers import CustomUserManager
from django.utils.translation import gettext_lazy as _


class User(AbstractBaseUser, PermissionsMixin):
    full_name = models.CharField(max_length=255, verbose_name="ФИО")
    username = models.CharField(_('username'), max_length=30, unique=True)
    password = models.CharField(_('password'), max_length=128)
    department = models.ForeignKey('Department', on_delete=models.CASCADE, null=True, blank=True, related_name='Filial')
    date_joined = models.DateTimeField(default=timezone.now, null=True)
    is_viewer = models.BooleanField(default=False)

    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('employee', 'Employee'),
        ('accountant', 'Accountant'),
    ]

    role = models.CharField(max_length=10, choices=ROLE_CHOICES, null=True, blank=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'username'

    class Meta:
        verbose_name_plural = 'Users'

    def __str__(self):
        return f'{self.username}'



class Department(models.Model):
    dep_name = models.CharField(max_length=350)

    class Meta:
        verbose_name_plural = 'Department'

    def __str__(self):
        return f'{self.dep_name}'
