from flask_sqlalchemy import SQLAlchemy
from geoalchemy2 import Geometry
from sqlalchemy.dialects.postgresql import UUID
import uuid

db = SQLAlchemy()

class GeoBucket(db.Model):
    __tablename__ = 'geo_buckets'
    # Use Google's unique Place ID as the primary identifier for normalization
    id = db.Column(db.String(255), primary_key=True) 
    name = db.Column(db.String(255), nullable=False)
    # PostGIS geometry for spatial stats/boundaries
    center = db.Column(Geometry('POINT', srid=4326)) 

class Property(db.Model):
    __tablename__ = 'properties'
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = db.Column(db.String(255), nullable=False)
    location_name = db.Column(db.String(255))
    price = db.Column(db.Float)
    bedrooms = db.Column(db.Integer)
    bathrooms = db.Column(db.Integer)
    # Geo-location of the property itself
    geom = db.Column(Geometry('POINT', srid=4326), nullable=False)
    
    # The "Geo-Bucket" link
    bucket_id = db.Column(db.String(255), db.ForeignKey('geo_buckets.id'), nullable=False)
    bucket = db.relationship('GeoBucket', backref=db.backref('properties', lazy=True))