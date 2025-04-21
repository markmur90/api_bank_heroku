from django.urls import path, include
from django.views.generic import TemplateView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    obtener_datos,
    realizar_transferencia,
    realizar_transferencia_real,
    realizar_transferencia_simulada,
    descargar_pdf
)

urlpatterns = [
    path('datos/', obtener_datos, name='obtener_datos'),  # Obtener datos
    path('transferir/', realizar_transferencia, name='realizar_transferencia'),  # Realizar transferencia
    path('transferir-real/', realizar_transferencia_real, name='transferencia_real'),  # Realizar transferencia real
    path('transferir-simulado/', realizar_transferencia_simulada, name='transferencia_simulada'),  # Realizar transferencia simulada
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),  # Obtener token JWT
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),  # Refrescar token
    path('descargar-pdf/<str:referencia>/', descargar_pdf, name='descargar_pdf'),  # Descargar PDF de transferencia
    path('formulario/', TemplateView.as_view(template_name="transfer_form.html"), name='transfer_form'),  # Servir el formulario HTML
    path('o/', include('oauth2_provider.urls', namespace='oauth2_provider')),
]
 
#datos/: Ruta para obtener datos generales.
#transferir/: Ruta para realizar una transferencia.
#transferir-real/: Ruta para realizar una transferencia real.
#transferir-simulado/: Ruta para realizar una transferencia simulada.
#token/: Ruta para obtener un token JWT.
#token/refresh/: Ruta para refrescar un token JWT.
#descargar-pdf/<str:referencia>/: Ruta para descargar el PDF de una