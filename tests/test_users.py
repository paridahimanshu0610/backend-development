import pytest
from jose import jwt
from app import models

from app.config import settings


# def test_root(client):

#     res = client.get("/")
#     print(res.json().get('message'))
#     assert res.json().get('message') == 'Hello World'
#     assert res.status_code == 200


def test_create_user(client):
    res = client.post("/user/", json={"username": "testuser123", "full_name": "testuser123", "email": "testuser123@gmail.com", "password": "password123"})

    print("user output")
    print(res.json())
    new_user = models.ReadUser(**res.json())

    assert new_user.email == "testuser123@gmail.com"
    assert res.status_code == 201


def test_login_user(test_user, client):
    res = client.post(
        "/login", data={"username": test_user['email'], "password": test_user['password']})
    login_res = models.Token(**res.json())
    payload = jwt.decode(login_res.access_token,
                         settings.secret_key, algorithms=[settings.algorithm])
    id = payload.get("user_id")
    assert id == test_user['id']
    assert login_res.token_type == "bearer"
    assert res.status_code == 200


@pytest.mark.parametrize("email, password, status_code", [
    ('incorrectemail@gmail.com', 'password123', 401),
    ('tim@gmail.com', 'incorrectpassword', 401),
    ('incorrectemail@gmail.com', 'incorrectpassword', 401),
    (None, 'password123', 422),
    ('tim@gmail.com', None, 422)
])
def test_incorrect_login(test_user, client, email, password, status_code):
    res = client.post(
        "/login", data={"username": email, "password": password})

    assert res.status_code == status_code
    # assert res.json().get('detail') == 'Invalid Credentials'
