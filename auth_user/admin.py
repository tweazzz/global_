from django.contrib import admin

# Register your models here.
from .models import User, Department

admin.site.register(User)
admin.site.register(Department)