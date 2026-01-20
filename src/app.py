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

def get_normalized_name(location_input):
    """
    Helper to extract a consistent neighborhood/locality name 
    regardless of how specific the search string is.
    """
    geocode_result = gmaps.geocode(location_input)
    if not geocode_result:
        return None
    
    components = geocode_result[0]['address_components']
    
    # Priority 1: Look for 'neighborhood' (e.g., Sangotedo)
    # Priority 2: Look for 'sublocality_level_1' (e.g., Ajah)
    # Priority 3: Fall back to 'locality' (e.g., Lagos)
    for target in ['neighborhood', 'sublocality_level_1', 'locality']:
        for component in components:
            if target in component['types']:
                return component['long_name']
                
    # Final fallback: Use the formatted address if no components match
    return geocode_result[0]['formatted_address']

def get_neighborhood_data(lat, lng):
    """
    Helper to extract a consistent neighborhood name and a representative 
    Place ID from coordinates.
    """
    # Look for neighborhood or sublocality
    results = gmaps.reverse_geocode((lat, lng))
    
    if not results:
        return None, None

    # We want to find a consistent 'bucket name' from the address components
    components = results[0]['address_components']
    normalized_name = None
    
    # Priority: neighborhood -> sublocality_level_1 -> locality
    for target in ['neighborhood', 'sublocality_level_1', 'locality']:
        for component in components:
            if target in component['types']:
                normalized_name = component['long_name']
                break
        if normalized_name: break

    # If no neighborhood name found, fall back to formatted address
    if not normalized_name:
        normalized_name = results[0]['formatted_address']

    # Use a stable ID. Even if the results[0] place_id varies slightly, 
    # we will link properties by the NAME of the bucket in the next step.
    # However, for the DB Primary Key, the first result's place_id is fine.
    return normalized_name, results[0]['place_id']

def get_bucket_resolution(input_data, is_coords=False):
    """
    Standardized function to find a bucket name.
    input_data: either (lat, lng) tuple or "address string"
    """
    if is_coords:
        results = gmaps.reverse_geocode(input_data)
    else:
        results = gmaps.geocode(input_data)
    
    if not results:
        return None, None

    # We want the MOST SPECIFIC neighborhood-level name available
    components = results[0]['address_components']
    name = None
    
    # Define the 'Bucket Granularity' we want
    # We look for neighborhood first, then sublocality
    for target in ['neighborhood', 'sublocality_level_1', 'sublocality']:
        for component in components:
            if target in component['types']:
                name = component['long_name']
                app.logger.info(f"Found {target}: {name}")
                break
        if name: break

    # Fallback: if no neighborhood is found, use the locality (e.g., Eti-Osa)
    if not name:
        for component in components:
            if 'locality' in component['types'] or 'administrative_area_level_2' in component['types']:
                name = component['long_name']
                break
                
    return name, results[0]['place_id']


@app.route('/api/properties', methods=['POST'])
def create_property():
    data = request.json
    
    # Validation to prevent 500 errors
    if not all(k in data for k in ('lat', 'lng', 'title')):
        return jsonify({"error": "Missing required fields: lat, lng, title"}), 400

    lat, lng = data['lat'], data['lng']
    location_input = data.get('location') or data.get('location_name')
    
    # Get the Normalized Neighborhood Name, with is_coords=True
    normalized_name, place_id = get_bucket_resolution((lat, lng), is_coords=True)
    
    if not normalized_name:
        return jsonify({"error": "Could not resolve location via Google Maps"}), 400

    app.logger.info(f"Input: {location_input} -> Normalized Bucket: {normalized_name}")

    # Check if a bucket with this NAME already exists
    # This is the "Geo-Bucket" logic: grouping by the neighborhood name
    bucket = GeoBucket.query.filter(GeoBucket.name.ilike(normalized_name)).first()
    
    if not bucket:
        # Create new bucket if this neighborhood is new to our DB
        bucket = GeoBucket(
            id=place_id, # Use the Google Place ID as the unique PK
            name=normalized_name,
            center=from_shape(Point(lng, lat), srid=4326)
        )
        db.session.add(bucket)
        db.session.flush() # Flush to get the ID if needed before commit

    # Create Property linked to the bucket
    new_prop = Property(
        title=data['title'],
        location_name=location_input,
        price=data.get('price'),
        bedrooms=data.get('bedrooms'),
        bathrooms=data.get('bathrooms'),
        geom=from_shape(Point(lng, lat), srid=4326),
        bucket_id=bucket.id # Link to the found or created bucket
    )
    
    db.session.add(new_prop)
    db.session.commit()
    
    return jsonify({
        "message": "Property created", 
        "bucket": bucket.name,
        "bucket_id": bucket.id
    }), 201

@app.route('/api/properties/search', methods=['GET'])
def search_properties():
    location_query = request.args.get('location')
    app.logger.info(f"--- Search Request for: {location_query} ---")
    
    # Normalize the query to a Neighborhood name
    # Use the SAME helper with is_coords=False
    normalized_bucket_name, _ = get_bucket_resolution(location_query, is_coords=False)
    
    app.logger.info(f"Search '{location_query}' resolved to Bucket: {normalized_bucket_name}")
    
    if not normalized_bucket_name:
        return jsonify([]), 200
    
    # Efficient lookup: Find the bucket by name, then get all its properties
    # We use ILIKE for case-insensitive matching in case of manual DB entries
    bucket = GeoBucket.query.filter(GeoBucket.name.ilike(normalized_bucket_name)).first()
    
    if not bucket:
        app.logger.info(f"No bucket found in database for {normalized_bucket_name}")
        return jsonify([]), 200
        
    properties = Property.query.filter_by(bucket_id=bucket.id).all()
    
    app.logger.info(f"Found {len(properties)} properties in bucket {bucket.name}")
    
    return jsonify([{
        "title": p.title, 
        "location": p.location_name,
        "bucket": p.bucket.name,
        "coordinates": {"lat": p.lat, "lng": p.lng} # Good for debugging
    } for p in properties])

@app.route('/api/geo-buckets/stats', methods=['GET'])
def get_stats():
    # Returns total buckets and property distribution
    stats = db.session.query(
        GeoBucket.name, 
        db.func.count(Property.id)
    ).join(Property).group_by(GeoBucket.name).all()

    app.logger.info(stats)
    
    return jsonify({str(name): count for name, count in stats})