# ExpertListing: Geo-Bucket Backend

This system implements a location normalization engine using "Geo-Buckets" to group properties by neighborhood, solving the problem of inconsistent search results due to coordinate variations or naming typos.

## Prerequisites

* **Python 3.9+**
* 
**Docker & Docker Compose** (Recommended for PostGIS setup) 


* **Google Maps API Key** (with Geocoding API enabled)

## 1. Environment Configuration

Create a `.env` file in the root directory and add the following:

```env
FLASK_APP=src/app.py
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/expertlisting
GOOGLE_MAPS_API_KEY=your_api_key_here

```

## 2. Database Setup (PostGIS)

The project requires **PostgreSQL with the PostGIS extension**. The easiest way to run this is via Docker:

```bash
# Pull and run the PostGIS image
docker run --name expertlisting-db \
  -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=expertlisting \
  -p 5432:5432 \
  -d postgis/postgis

```

## 3. Installation

1. **Clone the repository:**
```bash
git clone <your-repo-url>
cd expertlisting-backend

```


2. **Create a virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

```


3. **Install dependencies:**
```bash
pip install -r requirements.txt

```



## 4. Initialize Database

Run the following commands to initialize the database schema and create the necessary tables:

```bash
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

```

## 5. Running the Application

Start the Flask development server:

```bash
flask run

```

The API will be available at `http://localhost:5000`.

## 6. Seeding & Testing (The "Sangotedo" Case)

To verify the system, run the seed script which executes the required assessment test cases:

```bash
python src/seed.py

```

### Manual Verification

You can manually test the normalization by running these requests in order:

1. 
**Create Properties** (Different names/coordinates):


```bash
curl -X POST http://localhost:5000/api/properties \
-H "Content-Type: application/json" \
-d '{"title": "House 1", "location_name": "Sangotedo", "lat": 6.4698, "lng": 3.6285}'

curl -X POST http://localhost:5000/api/properties \
-H "Content-Type: application/json" \
-d '{"title": "House 2", "location_name": "Sangotedo, Ajah", "lat": 6.4720, "lng": 3.6301}'

```


2. 
**Search Properties** (Should return all results from the same bucket):


```bash
curl "http://localhost:5000/api/properties/search?location=sangotedo"

```


3. 
**Check Bucket Stats**:


```bash
curl "http://localhost:5000/api/geo-buckets/stats"

```



## 7. Running Tests

Run the automated test suite to verify location matching and API integrity:

```bash
pytest tests/

```

---

Key Endpoints 

* 
`POST /api/properties`: Accepts property details and auto-assigns a geo-bucket.


* 
`GET /api/properties/search?location=`: Performs a bucket-based lookup for properties.


* 
`GET /api/geo-buckets/stats`: Returns system-wide bucket coverage and property counts.