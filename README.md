#Book Review API

## Overview

This is a comprehensive book review service built with FastAPI and PostgreSQL. The application provides RESTful endpoints for managing books and reviews with caching, pagination, search functionality, and a web interface. It demonstrates modern Python backend development practices including database integration, caching strategies, comprehensive testing, and API documentation.

## System Architecture

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs with Python
- **SQLAlchemy**: SQL toolkit and Object-Relational Mapping (ORM) library
- **Alembic**: Database migration tool for managing schema changes
- **Pydantic**: Data validation and settings management using Python type annotations

### Database Design
- **Primary Database**: PostgreSQL with connection pooling and health checks
- **ORM Models**: Two main entities (Books and Reviews) with proper relationships
- **Indexing Strategy**: Optimized indexes on frequently queried fields (book_id, rating, created_at)
- **Migration Management**: Alembic for version-controlled database schema changes

### Caching Layer
- **Redis**: In-memory cache for improved performance
- **Cache Strategy**: Cache-first approach with graceful degradation when cache is unavailable
- **TTL Configuration**: Configurable cache expiration (default 5 minutes)
- **Cache Keys**: Structured cache keys for books and reviews with pagination parameters

## Key Components

### API Endpoints
- `GET /api/books` - List books with pagination, search, and caching
- `POST /api/books` - Create new books with validation
- `GET /api/books/{id}/reviews` - Get reviews for a specific book
- `POST /api/books/{id}/reviews` - Add reviews to books
- `GET /` - Web interface for interacting with the API

### Data Models
- **Book**: Core entity with title, author, ISBN, description, and publication year
- **Review**: Rating and text reviews linked to books with reviewer information
- **Relationships**: One-to-many relationship between books and reviews with cascade deletion

### Validation & Schemas
- **Pydantic Schemas**: Comprehensive input validation and serialization
- **Rating Validation**: Ensures ratings are between 1.0 and 5.0
- **Email Validation**: Optional email validation for reviewers
- **Pagination**: Configurable page size with reasonable limits

### Error Handling
- **HTTP Status Codes**: Proper REST status codes for different scenarios
- **Validation Errors**: Detailed error messages for invalid input
- **Cache Failure Handling**: Graceful degradation when Redis is unavailable
- **Database Error Handling**: Connection error handling with retry logic

## Data Flow

### Book Retrieval Flow
1. API request received with pagination/search parameters
2. Generate cache key based on request parameters
3. Check Redis cache for existing data
4. If cache miss, query PostgreSQL database
5. Store results in cache with TTL
6. Return paginated response with metadata

### Review Creation Flow
1. Validate book existence in database
2. Validate review data (rating, email format, etc.)
3. Create review record in database
4. Invalidate related cache entries
5. Return created review with metadata

### Cache Management
- **Cache Keys**: Structured format including entity type, parameters, and filters
- **Invalidation**: Strategic cache invalidation on data modifications
- **Fallback**: Automatic fallback to database when cache is unavailable

## External Dependencies

### Required Services
- **PostgreSQL**: Primary data storage
- **Redis**: Caching layer (optional, graceful degradation)

### Python Packages
- **FastAPI**: Web framework and API documentation
- **SQLAlchemy**: Database ORM and connection management
- **Alembic**: Database migration management
- **Redis**: Cache client library
- **Pydantic**: Data validation and configuration
- **Uvicorn**: ASGI server for running the application

### Frontend Dependencies
- **Bootstrap**: UI framework for responsive design
- **Font Awesome**: Icon library for enhanced UI
- **Vanilla JavaScript**: Client-side API interaction

## Deployment Strategy

### Environment Configuration
- **Environment Variables**: Database URL, Redis URL, cache TTL, debug mode
- **Settings Management**: Centralized configuration using Pydantic Settings
- **Default Values**: Sensible defaults for development environment

### Database Setup
- **Migrations**: Alembic migrations for database schema management
- **Connection Pooling**: SQLAlchemy connection pooling for performance
- **Health Checks**: Database connection health monitoring

### Application Startup
- **Table Creation**: Automatic table creation for development
- **Static Files**: Serving static assets for web interface
- **CORS Configuration**: Permissive CORS for development (should be restricted in production)

### Testing Infrastructure
- **Unit Tests**: Comprehensive tests for business logic
- **Integration Tests**: End-to-end API testing with test database
- **Cache Testing**: Mock Redis testing for cache functionality
- **Fixtures**: Reusable test data and database setup

## Database Setup Instructions

To connect to an online PostgreSQL database:

1. **Choose a PostgreSQL hosting provider:**
   - Supabase (recommended for assignments): supabase.com
   - Neon: neon.tech
   - ElephantSQL: elephantsql.com
   - Railway: railway.app

2. **Get your database connection string:**
   - Format: `postgresql://username:password@host:port/database_name`
   - Example: `postgresql://user:pass123@aws-0-us-east-1.pooler.supabase.com:5432/postgres`

3. **Set the DATABASE_URL environment variable:**
   - The application is already configured to use this variable
   - Just replace the current DATABASE_URL with your online database URL

4. **Test the connection:**
   - The application will automatically create tables on startup
   - Check the health endpoint at `/health` to verify API status

## Technology Stack

- **Backend**: Flask (Python)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Caching**: Redis (optional)
- **Frontend**: Vanilla JavaScript with basic CSS
- **Server**: Gunicorn WSGI server

## Setup Instructions

### 1. Prerequisites
- Python 3.11+
- PostgreSQL database (local or online)
- Redis (optional, for caching)

### 🚀 Starting Redis Server

Before launching the app, make sure **Redis server** is up and running.
On Windows (if installed via Redis MSI or Chocolatey):
redis-server

 ### Run the Application
You can either run the app directly or using a virtual environment.

🔹 Method 1: Directly with pip
1. Install dependencies
```bash
pip install fastapi flask flask-sqlalchemy gunicorn redis psycopg2-binary sqlalchemy alembic uvicorn[standard] pydantic==1.10.13 pydantic-settings email-validator pytest pytest-asyncio python-multipart PyYAML==6.0
```
2. Apply database migrations

  alembic upgrade head

3. Run the FastAPI app

  uvicorn app:app --reload

🔹 Method 2: Using venv (Recommended)
1. Create & activate virtual environment

python -m venv venv
# On Linux/macOS:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

2. Install all dependencies
```bash
pip install fastapi flask flask-sqlalchemy gunicorn redis psycopg2-binary sqlalchemy alembic uvicorn[standard] pydantic==1.10.13 pydantic-settings email-validator pytest pytest-asyncio python-multipart PyYAML==6.0
```
3. Run Alembic migrations

alembic upgrade head

4. Start the development server

uvicorn app:app --reload

## 📖 API Documentation
Swagger UI → http://localhost:8000/docs

🧪 Run Tests
bash
Copy code
pytest
✅ Unit tests for two core endpoints

🔄 Integration test validating cache-miss Redis fallback

🧱 Database
ORM: SQLAlchemy

Migration Tool: Alembic

Indexed fields on:

books.id, books.title, books.author, books.isbn

reviews.book_id, reviews.rating, reviews.created_at

## 📂 Project Structure
```bash
.
├── app.py                  # Main FastAPI entrypoint
├── config.py               # Settings via pydantic-settings
├── database.py             # DB engine, session, and Base
├── models/                 # SQLAlchemy models
├── routes/                 # API routes for books & reviews
├── templates/              # Jinja2 HTML templates
├── static/                 # CSS + JS frontend
├── alembic/                # DB migration tool
│   └── versions/
│       └── 001_initial_migration.py
├── tests/                  # Unit and integration tests
├── pyproject.toml
└── README.md → http://localhost:8000/docs

```

### 2. Installation

```bash
# Clone the repository
git clone https://github.com/luvmalani/book-review-system.git
cd book-review-system

# Install dependencies
pip install -r requirements.txt
```

### 3. Database Configuration

Set your database connection URL as an environment variable:

```bash
export DATABASE_URL="postgresql://username:password@host:port/database_name"
```

For online PostgreSQL providers:
- **Supabase**: Get connection string from project settings
- **Neon**: Copy connection URL from dashboard
- **ElephantSQL**: Use provided connection URL

### 4. Optional: Redis Configuration

```bash
export REDIS_URL="redis://localhost:6379/0"
```

### 5. Run the Application

```bash
# Start the server
gunicorn --bind 0.0.0.0:5000 --reuse-port --reload main:app

# Or for development
python flask_app.py
```

The application will be available at `http://localhost:5000`

## Usage

### Web Interface
1. Open `http://localhost:5000` in your browser
2. Add books using the "Add New Book" button
3. Click on any book to view and add reviews
4. Use the search box to find specific books

### API Usage Examples

**Create a book:**
```bash
curl -X POST http://localhost:5000/api/books \
  -H "Content-Type: application/json" \
  -d '{
    "title": "The Great Gatsby",
    "author": "F. Scott Fitzgerald",
    "isbn": "9780743273565",
    "publication_year": 1925
  }'
```

**Add a review:**
```bash
curl -X POST http://localhost:5000/api/books/1/reviews \
  -H "Content-Type: application/json" \
  -d '{
    "reviewer_name": "John Doe",
    "rating": 4.5,
    "review_text": "Great book!"
  }'
```

**Get books:**
```bash
curl http://localhost:5000/api/books?page=1&size=10&search=gatsby
```

## Project Structure

```
book-review-system/
├── flask_app.py          # Main Flask application
├── models.py             # Database models
├── config.py             # Application configuration
├── cache.py              # Redis caching service
├── database.py           # Database connection
├── templates/
│   └── index.html        # Web interface
├── static/
│   ├── style.css         # Frontend styling
│   └── app.js           # Frontend JavaScript
├── tests/               # Test files
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Database Schema

### Books Table
- `id`: Primary key
- `title`: Book title (required)
- `author`: Author name (required)
- `isbn`: ISBN number (optional)
- `description`: Book description (optional)
- `publication_year`: Year published (optional)
- `created_at`, `updated_at`: Timestamps

### Reviews Table
- `id`: Primary key
- `book_id`: Foreign key to books table
- `reviewer_name`: Name of reviewer (required)
- `reviewer_email`: Email address (optional)
- `rating`: Rating from 1.0 to 5.0 (required)
- `review_text`: Review content (optional)
- `created_at`, `updated_at`: Timestamps

## Features in Detail

### Caching
- Redis caching with 5-minute TTL
- Graceful fallback when Redis unavailable
- Cache invalidation on data updates

### Search
- Full-text search across book titles and authors
- Case-insensitive matching
- Pagination support for search results

### Validation
- Input validation using Pydantic schemas
- Email format validation
- Rating range validation (1.0-5.0)
- Required field validation

### Error Handling
- Comprehensive error responses
- Database connection error handling
- Cache failure graceful degradation

## Development

### Running Tests
```bash
python -m pytest tests/
```

### Environment Variables
- `DATABASE_URL`: PostgreSQL connection string (required)
- `REDIS_URL`: Redis connection string (optional)
- `SESSION_SECRET`: Flask session secret key
- `DEBUG`: Enable debug mode (default: True)

## License

This project is for educational/assessment purposes.

## Contact

GitHub: [@luvmalani](https://github.com/luvmalani)
