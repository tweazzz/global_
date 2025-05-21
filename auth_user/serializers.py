from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        # Добавляем роль в ответ
        data['role'] = self.user.role
        return data



class UserSerializer(serializers.ModelSerializer):
     class Meta:
       model = User
       exclude = ['password']
