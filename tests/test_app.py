import pytest
from src.app import app, db

# @pytest.fixture
# def client():
#     app.config['TESTING'] = True
#     app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:' # Use in-memory DB for speed
#     with app.test_client() as client:
#         with app.app_context():
#             db.create_all()
#             yield client
#             db.drop_all()

# def test_property_creation_and_normalization(client):
#     """
#     Test 1: Prove that creating a property auto-assigns it to a bucket.
#     """
#     payload = {
#         "title": "Test Villa",
#         "location": "Sangotedo",
#         "lat": 6.4698,
#         "lng": 3.6285
#     }
#     response = client.post('/api/properties', json=payload)
#     assert response.status_code == 201
    
#     data = response.get_json()
#     assert "bucket" in data
#     assert data["bucket"] != ""

# def test_sangotedo_grouping(client):
#     """
#     Test 2: Prove that different names for the same area result in the same bucket.
#     This directly addresses the core problem in the task specification.
#     """
#     # Create two properties with different location strings but same area
#     p1 = {"title": "House A", "location": "Sangotedo", "lat": 6.4698, "lng": 3.6285}
#     p2 = {"title": "House B", "location": "Sangotedo, Ajah", "lat": 6.4720, "lng": 3.6301}
    
#     client.post('/api/properties', json=p1)
#     client.post('/api/properties', json=p2)
    
#     # Search for the generic name
#     response = client.get('/api/properties/search?location=sangotedo')
#     results = response.get_json()
    
#     # Should find both because they were normalized into the same bucket
#     assert len(results) == 2
#     assert results[0]['bucket'] == results[1]['bucket']

# def test_bucket_stats(client):
#     """
#     Test 3: Prove that the stats endpoint correctly counts property distribution.
#     """
#     # Add one property
#     client.post('/api/properties', json={
#         "title": "Stat House",
#         "location": "Lekki",
#         "lat": 6.4474,
#         "lng": 3.4722
#     })
    
#     response = client.get('/api/geo-buckets/stats')
#     stats = response.get_json()
    
#     assert len(stats) >= 1
#     # Check if the count for the neighborhood is at least 1
#     counts = list(stats.values())
#     assert any(count >= 1 for count in counts)