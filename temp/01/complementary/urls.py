from django.urls import path
from core.complementary import views

urlpatterns = [
    path('error_response/', views.error_response_view, name='error_response'),
    path('message/', views.message_view, name='message'),
    path('transaction_status/', views.transaction_status_view, name='transaction_status'),
    path('status_response/', views.status_response_view, name='status_response'),
]
