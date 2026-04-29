import requests

BASE_URL = "http://localhost:8001/api"
LOGIN_DATA = {"username": "admin", "password": "admin123"}

def test_flow():
    # 1. Login
    print("Attempting login...")
    response = requests.post(f"{BASE_URL}/auth/token", data=LOGIN_DATA)
    if response.status_code != 200:
        print(f"Login failed: {response.text}")
        return
    
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Login successful.")

    # 2. Import materials
    print("Importing materials...")
    response = requests.post(f"{BASE_URL}/inventory/import", headers=headers)
    if response.status_code == 200:
        result = response.json()
        print(f"Import results: Success={result['success']}, Failed={result['failed']}")
    else:
        print(f"Import failed: {response.text}")

    # 3. Search materials
    print("Searching for materials...")
    response = requests.get(f"{BASE_URL}/materials/", headers=headers, params={"limit": 5})
    if response.status_code == 200:
        materials = response.json()
        print(f"Found {len(materials)} materials.")
        for m in materials:
            print(f"- {m['code']}: {m['name']}")
        
        if materials:
            target_id = materials[0]['id']
            # 4. Create inventory record
            print(f"Creating inventory record for material ID {target_id}...")
            record_data = {"material_id": target_id, "score": 5}
            response = requests.post(f"{BASE_URL}/inventory/records", headers=headers, json=record_data)
            if response.status_code == 200:
                print("Inventory record created successfully.")
            else:
                print(f"Failed to create record: {response.text}")
    else:
        print(f"Search failed: {response.text}")

if __name__ == "__main__":
    test_flow()
