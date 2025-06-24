# reestr/serializers.py

from rest_framework import serializers
from .models import Reestr
from auth_user.models import Department
from auth_user.serializers import UserReadSerializer,DepartmentSerializer


class ReestrReadSerializer(serializers.ModelSerializer):
    executor = UserReadSerializer()
    department = DepartmentSerializer()

    class Meta:
        model = Reestr
        fields = '__all__'


class ReestrWriteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reestr
        fields = '__all__'
