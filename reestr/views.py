# reestr/views.py
from rest_framework import viewsets, permissions
from .models import Reestr
from .serializers import ReestrReadSerializer,ReestrWriteSerializer
from auth_user.permission import CanOnlyAccountantUpdateIsPaid, IsAdminOnly


class ReestrViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated, CanOnlyAccountantUpdateIsPaid]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'employee':
            return Reestr.objects.filter(executor=user).order_by('-created_at')
        return Reestr.objects.all().order_by('-created_at')

    def get_serializer_class(self):
        if self.action in ['list', 'retrieve']:
            return ReestrReadSerializer
        return ReestrWriteSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'employee':
            serializer.save(executor=user)
        else:
            serializer.save()

