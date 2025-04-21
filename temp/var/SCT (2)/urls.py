from django.urls import path
from .views import SepaCreditTransferViewSet

transfer_view = SepaCreditTransferViewSet.as_view({
    'post': 'create',
    'get': 'list',
})

transfer_detail_view = SepaCreditTransferViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy',
})

urlpatterns = [
    path('transfers/', transfer_view, name='transfer-list'),
    path('transfers/<uuid:pk>/', transfer_detail_view, name='transfer-detail'),
]
