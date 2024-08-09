from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from app.database import close_mongo_connection, connect_to_mongo
from main import app


client = TestClient(app)
    
def test_signup():
    connect_to_mongo()
    response = client.post(
        "/api/v1/signup",  # replace with your actual signup endpoint
        json={
            "email": "testuser",
            "password": "testpassword",
            "phone": "1234567890",  # replace with actual phone number
            "type": "user",  # replace with actual user type
            "two_factor": "enabled",  # replace with actual two factor authentication status
            "registrationDate": "2022-01-01T00:00:00",  # replace with actual registration date in ISO 8601 format
            "approved": True,  # replace with actual approved status
            "version": 1,  # replace with actual version
        },
    )
    assert response.status_code == 200
    assert "id" in response.json()
    assert "email" in response.json()
    close_mongo_connection()



@pytest.mark.parametrize(
    "email, password, status_code",
    [("testuser", "wrongpassword", 400), ("wronguser", "testpassword", 200)],
)
def test_signup_error(email, password, status_code):
    connect_to_mongo()
    response = client.post(
        "/api/v1/signup",  # replace with your actual signup endpoint
        json={
            "email": email,
            "password": password,
            "phone": "1234567890",  # replace with actual phone number
            "type": "user",  # replace with actual user type
            "two_factor": "enabled",  # replace with actual two factor authentication status
            "registrationDate": "2022-01-01T00:00:00",  # replace with actual registration date in ISO 8601 format
            "approved": True,  # replace with actual approved status
            "version": 1,  # replace with actual version
        },
    )
    assert response.status_code == status_code
    close_mongo_connection()
    

def test_login():
    connect_to_mongo()
    response = client.post(
        "/api/v1/login",  # replace with your actual login endpoint
        data={
            "username": "testuser",
            "password": "testpassword",
        },
    )
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "refresh_token" in response.json()
    close_mongo_connection()


@pytest.mark.parametrize(
    "username, password, status_code",
    [("testuser", "wrongpassword", 400), ("wronguser", "testpassword", 200)],
)
def test_login_error(username, password, status_code):
    connect_to_mongo()
    response = client.post(
        "/api/v1/login",  # replace with your actual login endpoint
        data={
            "username": username,
            "password": password,
        },
    )
    assert response.status_code == status_code
    close_mongo_connection()
    

def test_get_me():
    connect_to_mongo()
    response = client.post(
        "/api/v1/login",  # replace with your actual login endpoint
        data={
            "username": "testuser",
            "password": "testpassword",
        },
    )
    access_token = response.json().get("access_token")
    close_mongo_connection()
    connect_to_mongo()
    # Then, use the access token to get the current user
    response = client.get(
        "/api/v1/me",  # replace with your actual /me endpoint
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200
    assert "id" in response.json()
    assert "email" in response.json()
    close_mongo_connection()
