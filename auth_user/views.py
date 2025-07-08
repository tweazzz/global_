from django.shortcuts import render
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer
from rest_framework import viewsets,permissions
from .models import User, Department
from .serializers import UserReadSerializer,UserWriteSerializer, DepartmentSerializer
from .permission import IsAdminOrAccountant, IsAdminOnly,IsAdminRoleOrReadOnly
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status
from .serializers import UserMeSerializer


class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve', 'me']:
            return UserReadSerializer
        return UserWriteSerializer

    def get_permissions(self):
        if self.action == 'me':
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOnly]
        return [permission() for permission in permission_classes]

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class DepartmentViewSet(viewsets.ModelViewSet):
    queryset = Department.objects.all()
    serializer_class = DepartmentSerializer
    permission_classes = [IsAdminRoleOrReadOnly]
    pagination_class = None
