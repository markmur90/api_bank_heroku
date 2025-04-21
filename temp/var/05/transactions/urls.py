from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TransferenciaViewSet

router = DefaultRouter()
router.register(r'transferencias', TransferenciaViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
