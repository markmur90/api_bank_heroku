import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User

@pytest.fixture
def api_client():
    return APIClient()

@pytest.fixture
def create_user(db):
    def make_user(username="testuser", password="testpass"):
        user = User.objects.create_user(username=username, password=password)
        return user
    return make_user
