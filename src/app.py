from flask import Flask, request, jsonify
from flask_migrate import Migrate
import googlemaps
from models import db, Property, GeoBucket
from geoalchemy2.shape import from_shape
from shapely.geometry import Point
import os

# extract env variables from environment
DATABASE_URL = os.getenv('DATABASE_URL')
GOOGLE_MAPS_API_KEY = os.getenv('GOOGLE_MAPS_API_KEY')

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
db.init_app(app)
migrate = Migrate(app, db)

gmaps = googlemaps.Client(key=GOOGLE_MAPS_API_KEY)

@app.route('/api/properties', methods=['POST'])
def create_property():
    data = request.json
    lat, lng = data['lat'], data['lng']
    
    # Use Google Maps to get a normalized Place ID (The Bucket)
    # Using reverse geocode on the coordinates, to find the "neighborhood" or "locality"
    result = gmaps.reverse_geocode((lat, lng), result_type='neighborhood')
    if not result:
        result = gmaps.reverse_geocode((lat, lng), result_type='locality')
        
    place_id = result[0]['place_id']
    normalized_name = result[0]['formatted_address']

    # Check if bucket exists, if not create it 
    bucket = GeoBucket.query.get(place_id)
    if not bucket:
        bucket = GeoBucket(
            id=place_id, 
            name=normalized_name,
            center=from_shape(Point(lng, lat), srid=4326)
        )
        db.session.add(bucket)

    # Create Property linked to the bucket
    new_prop = Property(
        title=data['title'],
        location_name=data['location_name'],
        price=data.get('price'),
        bedrooms=data.get('bedrooms'),
        bathrooms=data.get('bathrooms'),
        geom=from_shape(Point(lng, lat), srid=4326),
        bucket_id=place_id
    )
    db.session.add(new_prop)
    db.session.commit()
    
    return jsonify({"message": "Property created", "bucket": normalized_name}), 201

@app.route('/api/properties/search', methods=['GET'])
def search_properties():
    location_query = request.args.get('location')
    
    # Normalize the search query using Google to find the relevant bucket
    geocode_result = gmaps.geocode(location_query)
    if not geocode_result:
        return jsonify([]), 200
    
    target_place_id = geocode_result[0]['place_id']
    
    # Efficient lookup using the bucket ID instead of scanning all properties
    properties = Property.query.filter_by(bucket_id=target_place_id).all()
    
    return jsonify([{
        "title": p.title, 
        "location": p.location_name,
        "bucket": p.bucket.name
    } for p in properties])

@app.route('/api/geo-buckets/stats', methods=['GET'])
def get_stats():
    # Returns total buckets and property distribution
    stats = db.session.query(
        GeoBucket.name, 
        db.func.count(Property.id)
    ).join(Property).group_by(GeoBucket.name).all()
    
    return jsonify({str(name): count for name, count in stats})