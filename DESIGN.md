# Architecture Design: Geo-Bucket Normalization System

## 1. Geo-Bucket Strategy

The core challenge is resolving inconsistent location names (e.g., "Sangotedo" vs. "Sangotedo, Ajah") and slightly varied coordinates into a single logical entity to ensure search reliability.

### The Google Maps "Place ID" Approach

Instead of manual clustering algorithms, this system leverages the **Google Maps Geocoding API** to define buckets.

* 
**Definition of a Bucket**: A bucket is defined by a unique **Google Place ID** representing a specific neighborhood or locality.


* **Grouping Logic**: When a property is created, its coordinates or raw location string are sent to Google Maps. Google returns a standardized `place_id`. All properties sharing this ID are logically grouped into the same bucket.


* 
**Benefits**: This offloads the complexity of global address normalization and typo-tolerance to a proven third-party service, ensuring that "sangotedo lagos" and "Sangotedo" resolve to the same identifier.



## 2. Database Schema

The system uses **PostgreSQL with PostGIS** to handle both relational data and geographic indexing.

### Tables

1. **`geo_buckets`**:
* 
`id` (String, PK): The unique Google Place ID.


* 
`name` (String): The normalized address/neighborhood name from Google.


* 
`center` (Geography Point): The centroid coordinates of the bucket.




2. **`properties`**:
* 
`id` (UUID, PK): Unique property identifier.


* 
`bucket_id` (String, FK): Reference to `geo_buckets.id`.


* 
`location_name` (String): The original user-inputted name.


* 
`geom` (Geography Point): Precise coordinates of the property.


* 
`title`, `price`, `bedrooms`, `bathrooms`.





### Indexes

* 
**GIST Index** on `properties.geom` and `geo_buckets.center` for fast spatial queries.


* 
**B-Tree Index** on `properties.bucket_id` for O(1) retrieval of properties within a bucket.



## 3. Location Matching Logic

The system handles normalization through a two-step process:

1. 
**String & Coordinate Normalization**: During `POST /api/properties`, the system uses the Google Geocoding API to transform varied inputs into a single `place_id`.


2. **Bucket Lookup**: During `GET /api/properties/search`, the search term (e.g., "Sangotedo") is geocoded to find its `place_id`. The system then queries the `properties` table for that specific `bucket_id` rather than performing a full table scan or fuzzy text search.



## 4. System Flow Diagram

```text
[ User Search: "Sangotedo" ]
          |
          v
[ Google Maps API ] ----> Returns: { place_id: "ChIJuT...", name: "Sangotedo" }
          |
          v
[ PostgreSQL Query ] ---> SELECT * FROM properties WHERE bucket_id = 'ChIJuT...'
          |
          v
[cite_start][ Response: 47 Properties ] [cite: 6, 30]

```

5. Review Discussion Points 

### Why this approach?

Using Google Place IDs provides "Zero-Maintenance Normalization". It correctly identifies that "Sangotedo, Ajah" and "Sangotedo" are the same physical area without requiring complex custom regex or local neighborhood boundary data.

### Scaling to 500,000 Properties

* 
**Caching**: Cache the mapping of `search_string` -> `place_id` in Redis to minimize API costs and latency.


* 
**Database Indexing**: The use of the `bucket_id` foreign key ensures that lookups remain fast even as the property count grows, as it avoids expensive spatial "distance-from" calculations at read-time.



### Improvements with more time

* 
**Boundary Geometry**: Instead of just a center point, fetch and store the actual polygon boundaries for buckets to visualize "coverage" on a map.


* 
**Hybrid Search**: Implement a fallback to local Levenshtein string matching if the external API is unreachable.



### Alternative Approaches

* **Geohashing**: Dividing the map into a grid. This is cheaper (no API fees) but fails to account for natural neighborhood names/boundaries.


* **Local Clustering (K-Means)**: Grouping properties purely by coordinate proximity. This is difficult to scale as it requires re-calculating clusters when new properties are added.