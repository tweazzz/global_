from django.urls import path, include
from rest_framework.routers import DefaultRouter
from auth_user.views import UserViewSet,DepartmentViewSet
from .views import ReestrViewSet, ExcelUploadView


router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'reestr', ReestrViewSet, basename='reestr')
router.register(r'departments', DepartmentViewSet, basename='department')

urlpatterns = [
    path('', include(router.urls)),
    path('upload-excel/', ExcelUploadView.as_view(), name='upload-excel'),
]
