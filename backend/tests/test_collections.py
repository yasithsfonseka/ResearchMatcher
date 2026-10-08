from app.services.export_csv import sanitize_csv_field, generate_collection_csv

def test_csv_formula_injection_sanitization():
    unsafe_input = "=SUM(A1:A10)"
    sanitized = sanitize_csv_field(unsafe_input)
    assert sanitized == "'=SUM(A1:A10)"
    
    cmd_injection = "+cmd|' /C calc'!A0"
    sanitized_cmd = sanitize_csv_field(cmd_injection)
    assert sanitized_cmd.startswith("'")

def test_collections_api_flow(client):
    # Register & Login
    client.post("/api/v1/auth/register", json={
        "email": "colls@example.com",
        "password": "Password123!",
        "display_name": "Collection User"
    })
    token = client.post("/api/v1/auth/login", json={
        "email": "colls@example.com",
        "password": "Password123!"
    }).json()["access_token"]
    
    headers = {"Authorization": f"Bearer {token}"}

    # Create collection
    res_c = client.post("/api/v1/collections", json={
        "name": "Transformers Review",
        "description": "Literature review on modern transformer architectures"
    }, headers=headers)
    assert res_c.status_code == 201
    coll_id = res_c.json()["id"]

    # Export CSV (empty collection)
    res_export = client.get(f"/api/v1/collections/{coll_id}/export", headers=headers)
    assert res_export.status_code == 200
    assert "Title,DOI,Publication Year" in res_export.text
