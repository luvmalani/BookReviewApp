# Book Review System

A Flask-based book review API with PostgreSQL database and web interface for managing books and reviews.

## Features

- **Book Management**: Add, view, and search books
- **Review System**: Rate books from 1-5 stars with text reviews
- **Search**: Search books by title or author
- **Statistics**: View review statistics for each book
- **Pagination**: Browse through large collections of books and reviews
- **Caching**: Redis caching for improved performance (with graceful fallback)

## API Endpoints

### Books
- `GET /api/books` - List all books with pagination and search
- `POST /api/books` - Create a new book
- `GET /api/books/{id}` - Get specific book details

### Reviews
- `GET /api/books/{id}/reviews` - Get reviews for a specific book
- `POST /api/books/{id}/reviews` - Add a review to a book
- `GET /api/books/{id}/reviews/stats` - Get review statistics

### Health Check
- `GET /health` - API health status

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

📂 Project Structure
php
Copy code
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
