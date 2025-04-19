import pytest
from rest_framework.authtoken.models import Token
from api.transfers.models import Transfer
from unittest.mock import Mock

@pytest.fixture
def authenticated_client(api_client, create_user):
    user = create_user()
    token, _ = Token.objects.get_or_create(user=user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.key}")
    return api_client

@pytest.mark.django_db
def test_create_transfer_success(authenticated_client):
    """
    Prueba de creación exitosa de una transferencia.
    """
    data = {
        "source_account": "123456",
        "destination_account": "654321",
        "amount": "50.00",
        "currency": "EUR",
        "bank": "memo"
    }
    response = authenticated_client.post("/api/transfers/", data, format="json")

    assert response.status_code == 201
    assert Transfer.objects.count() == 1

@pytest.mark.django_db
def test_create_transfer_missing_field(authenticated_client):
    """
    Prueba de error por campo faltante en la solicitud de transferencia.
    """
    data = {
        "source_account": "123456",
        "amount": "50.00",
        "currency": "EUR",
        "bank": "memo"
    }
    response = authenticated_client.post("/api/transfers/", data, format="json")

    assert response.status_code == 400
    assert "destination_account" in response.data

@pytest.mark.django_db
def test_transfer_memo_bank_success(authenticated_client, mocker):
    """
    Simula una respuesta exitosa de Memo Bank en la transferencia.
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "transaction_id": "txn123456"
    }

    # Simula el request.post
    mocker.patch(
        "api.transfers.views.requests.post",
        return_value=mock_response
    )

    data = {
        "source_account": "123456",
        "destination_account": "654321",
        "amount": "50.00",
        "currency": "EUR",
        "bank": "memo"
    }
    response = authenticated_client.post("/api/transfers/", data, format="json")

    assert response.status_code == 200
    assert response.data["message"] == "Transfer successful"
    
@pytest.mark.django_db
def test_transfer_memo_bank_failure(authenticated_client, mocker):
    """
    Simula un fallo en la respuesta de Memo Bank.
    """
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.json.return_value = {"error": "Internal Server Error"}

    mocker.patch("api.transfers.views.requests.post", return_value=mock_response)

    data = {
        "source_account": "123456",
        "destination_account": "654321",
        "amount": "50.00",
        "currency": "EUR",
        "bank": "memo"
    }
    response = authenticated_client.post("/api/transfers/", data, format="json")

    assert response.status_code == 502
    assert response.data["error"] == "Bank service error"

@pytest.mark.django_db
def test_transfer_deutsche_bank_success(authenticated_client, mocker):
    """
    Simula una transferencia exitosa con Deutsche Bank.
    """
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "status": "success",
        "transaction_id": "DE123456"
    }

    mocker.patch("api.transfers.views.requests.post", return_value=mock_response)

    data = {
        "source_account": "123456",
        "destination_account": "654321",
        "amount": "100.00",
        "currency": "USD",
        "bank": "deutsche"
    }
    response = authenticated_client.post("/api/transfers/", data, format="json")

    assert response.status_code == 200
    assert response.data["transaction_id"] == "DE123456"
