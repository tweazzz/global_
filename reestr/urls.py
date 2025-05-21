from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ReestrViewSet

router = DefaultRouter()
router.register(r'reestr', ReestrViewSet, basename='reestr')

urlpatterns = [
    path('', include(router.urls)),
]
