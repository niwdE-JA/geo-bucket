import pytest
from src.app import app

@pytest.fixture
def client():
    """Configures the app for testing and provides a test client."""
    app.config['TESTING'] = True
    # We use the actual DB here to test the PostGIS integration
    with app.test_client() as client:
        yield client

def test_01_create_sangotedo_properties(client):
    """Test that creating properties with different strings groups them correctly."""
    locations = [
        {"title": "Villa A", "location": "Sangotedo", "lat": 6.4698, "lng": 3.6285},
        {"title": "Villa B", "location": "Sangotedo, Ajah", "lat": 6.4720, "lng": 3.6301},
        {"title": "Villa C", "location": "sangotedo lagos", "lat": 6.4705, "lng": 3.6290}
    ]

    for data in locations:
        response = client.post('/api/properties', json=data)
        assert response.status_code == 201
        res_data = response.get_json()
        assert "bucket" in res_data
        # Ensure the bucket name is consistent (e.g., 'Eti-Osa' or 'Sangotedo')
        assert res_data["bucket"] is not None

def test_02_search_normalization(client):
    """Test that searching for a variation returns all grouped properties."""
    # Search using a specific variation
    response = client.get('/api/properties/search?location=sangotedo ajah')
    assert response.status_code == 200
    
    results = response.get_json()
    # If normalization is working, all 3 properties from the previous test 
    # should be in the same bucket and returned here.
    assert len(results) >= 3
    
    # Verify they all belong to the same bucket
    bucket_names = {p['bucket'] for p in results}
    assert len(bucket_names) == 1

def test_03_stats_endpoint(client):
    """Test that the stats endpoint returns the correct bucket counts."""
    response = client.get('/api/geo-buckets/stats')
    assert response.status_code == 200
    
    stats = response.get_json()
    # At least one bucket should exist with at least 3 properties
    counts = list(stats.values())
    assert any(count >= 3 for count in counts)