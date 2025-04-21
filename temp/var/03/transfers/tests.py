from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

class TransfersURLTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_obtener_datos_url(self):
        response = self.client.get(reverse('obtener_datos'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertEqual(response.data, expected_data)

    def test_realizar_transferencia_url(self):
        response = self.client.post(reverse('realizar_transferencia'), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertEqual(response.data, expected_data)

    def test_realizar_transferencia_real_url(self):
        response = self.client.post(reverse('transferencia_real'), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertEqual(response.data, expected_data)

    def test_realizar_transferencia_simulada_url(self):
        response = self.client.post(reverse('transferencia_simulada'), data={})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertEqual(response.data, expected_data)

    def test_descargar_pdf_url(self):
        response = self.client.get(reverse('descargar_pdf', args=['ref123']))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertEqual(response.content, expected_content)

    def test_token_obtain_pair_url(self):
        response = self.client.post(reverse('token_obtain_pair'), data={'username': 'test', 'password': 'test'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertIn('access', response.data)
        # self.assertIn('refresh', response.data)
 
    def test_token_refresh_url(self):
        # Primero obtener un token de acceso y refresco
        response = self.client.post(reverse('token_obtain_pair'), data={'username': 'test', 'password': 'test'})
        refresh_token = response.data['refresh']
        # Luego usar el token de refresco para obtener un nuevo token de acceso
        response = self.client.post(reverse('token_refresh'), data={'refresh': refresh_token})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Agregar más aserciones según los datos esperados
        # self.assertIn('access', response.data)