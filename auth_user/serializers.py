from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from .models import User, Department


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        token['role'] = user.role
        return token

    def validate(self, attrs):
        data = super().validate(attrs)

        data['role'] = self.user.role
        return data


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = '__all__'

class UserReadSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer()
    class Meta:
        model = User
        fields = ['id', 'full_name', 'username', 'role', 'department', 'is_active']


class UserWriteSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    class Meta:
        model = User
        exclude = ['is_superuser', 'is_staff', 'groups', 'user_permissions']

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        request = self.context.get('request')
        if 'is_active' in validated_data and getattr(request.user, 'role', None) != 'admin':
            validated_data.pop('is_active')
        return super().update(instance, validated_data)


class UserMeSerializer(serializers.ModelSerializer):
    department = DepartmentSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'full_name', 'username', 'role', 'department', 'is_active']


