# Book Review API

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

## Changelog

Changelog:
- June 28, 2025. Initial setup with FastAPI and Bootstrap
- June 28, 2025. Converted to Flask application for Backend Engineer Assessment
- June 28, 2025. Simplified frontend styling to appear less AI-generated and more amateur
- June 28, 2025. Prepared for online PostgreSQL database connection

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

## User Preferences

Preferred communication style: Simple, everyday language.