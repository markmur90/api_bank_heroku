from django.urls import path
from . import views

urlpatterns = [
    path('', views.transferencia_view, name='transferencia'),
    path('exitosa/', views.transferencia_exitosa_view, name='transferencia_exitosa'),
    path('list/', views.transferencia_list_view, name='transferencia_list'),
    path('create/', views.transferencia_create_view, name='transferencia_create'),
    path('dashboard/', views.dashboard_transferencias_view, name='dashboard_transferencias'),
]
