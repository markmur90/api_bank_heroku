from django.urls import path
from . import views

app_name = 'gpt3'

urlpatterns = [
    path('transferencia/nueva/', views.enviar_transferencia, name='enviar_transferencia'),
    path('transferencia/<int:pk>/estado/', views.estado_transferencia, name='estado_transferencia'),
    path('transferencia/<int:pk>/retry/', views.retry_second_factor_view, name='retry_second_factor_view'),
    path('transferencia/<int:pk>/', views.detalle_transferencia, name='detalle_transferencia'),
    path('transferencia/', views.lista_transferencias, name='lista_transferencias'),
]