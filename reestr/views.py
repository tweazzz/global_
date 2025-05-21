# reestr/views.py

from rest_framework import viewsets, permissions
from .models import Reestr
from .serializers import ReestrEmployeeSerializer, ReestrSerializer

class ReestrViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.role == 'employee':
            return Reestr.objects.filter(executor=user)
        return Reestr.objects.all()

    def get_serializer_class(self):
        user = self.request.user
        if user.role in ['admin', 'accountant']:
            return ReestrSerializer
        return ReestrEmployeeSerializer

    def perform_create(self, serializer):
        user = self.request.user
        if user.role == 'employee':
            serializer.save(executor=user)
        else:
            serializer.save()
