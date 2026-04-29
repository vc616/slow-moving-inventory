import requests

BASE_URL = "http://localhost:8001/api"
LOGIN_DATA = {"username": "admin", "password": "admin123"}

def test_multi_keyword_search():
    # 1. Login
    response = requests.post(f"{BASE_URL}/auth/token", data=LOGIN_DATA)
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Search with multiple keywords (space separated)
    # Looking at previous results: "A01303: 滤芯"
    # Let's try searching for "A013 滤芯"
    print("Searching for 'A013 滤芯'...")
    response = requests.get(f"{BASE_URL}/materials/", headers=headers, params={"keyword": "A013 滤芯"})
    if response.status_code == 200:
        materials = response.json()
        print(f"Found {len(materials)} materials.")
        for m in materials:
            print(f"- {m['code']}: {m['name']}")
    else:
        print(f"Search failed: {response.text}")

    # 3. Search with non-matching keywords
    print("\nSearching for 'A013 隔膜' (should be empty or different)...")
    response = requests.get(f"{BASE_URL}/materials/", headers=headers, params={"keyword": "A013 隔膜"})
    if response.status_code == 200:
        materials = response.json()
        print(f"Found {len(materials)} materials.")
        for m in materials:
            print(f"- {m['code']}: {m['name']}")
    else:
        print(f"Search failed: {response.text}")

if __name__ == "__main__":
    test_multi_keyword_search()
