# reestr/serializers.py

from rest_framework import serializers
from .models import Reestr

class ReestrEmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reestr
        exclude = ['is_paid']


class ReestrSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reestr
        fields = '__all__'
