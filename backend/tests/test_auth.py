def test_register_login_flow(client):
    # Register
    reg_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!",
        "display_name": "Test Researcher"
    }
    res_reg = client.post("/api/v1/auth/register", json=reg_payload)
    assert res_reg.status_code == 201
    user_data = res_reg.json()
    assert user_data["email"] == "testuser@example.com"
    assert "password_hash" not in user_data

    # Login
    login_payload = {
        "email": "testuser@example.com",
        "password": "SecurePassword123!"
    }
    res_login = client.post("/api/v1/auth/login", json=login_payload)
    assert res_login.status_code == 200
    token_data = res_login.json()
    assert "access_token" in token_data
    token = token_data["access_token"]

    # Get Me
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/api/v1/auth/me", headers=headers)
    assert res_me.status_code == 200
    assert res_me.json()["display_name"] == "Test Researcher"
