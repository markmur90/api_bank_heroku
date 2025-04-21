import requests
from requests.exceptions import ConnectionError, Timeout
from config import settings

url = "http://127.0.0.1:8000/api/transferir-real/"

headers = {
    "Authorization": f"Bearer {settings.BEARER_TOKEN}"
}

try:
    response = requests.get(url, headers=headers, timeout=10)
    response.raise_for_status()  # Verifica si hay errores HTTP
    data = response.json()
    print(data)
except ConnectionError as e:
    print(f"Error de conexión: {e}")
except Timeout as e:
    print(f"Tiempo de espera agotado: {e}")
except requests.exceptions.RequestException as e:
    print(f"Error en la solicitud: {e}")