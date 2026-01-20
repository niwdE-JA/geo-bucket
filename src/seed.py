# To be run after database migration
import requests
import os

API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5000")

test_data = [
    {"title": "Villa A", "location": "Sangotedo", "lat": 6.4698, "lng": 3.6285},
    {"title": "Condo B", "location": "Sangotedo, Ajah", "lat": 6.4720, "lng": 3.6301},
    {"title": "Flat C", "location": "sangotedo lagos", "lat": 6.4705, "lng": 3.6290}
]

for item in test_data:
    requests.post(f"{API_BASE_URL}/api/properties", json=item)

# The verification search
response = requests.get(f"{API_BASE_URL}/api/properties/search?location=sangotedo")
print("Search Response:", response.json())
print(f"Properties found: {len(response.json())}") # Should be 3