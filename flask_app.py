import os
import logging
from flask import Flask, request, jsonify, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
import math

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "your-secret-key-change-in-production")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models after db initialization
from models import Book, Review

with app.app_context():
    db.create_all()

# Cache service import
from cache import cache_service

@app.route('/')
def index():
    """Serve the main HTML interface"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "book-review-api"})

@app.route('/api/books', methods=['GET'])
def get_books():
    """Get all books with pagination and optional search"""
    try:
        page = int(request.args.get('page', 1))
        size = min(int(request.args.get('size', 10)), 100)
        search = request.args.get('search')
        
        # Create cache key
        cache_key = f"books:page:{page}:size:{size}:search:{search or 'none'}"
        
        # Try to get from cache first
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for key: {cache_key}")
            return jsonify(cached_result)
        
        logger.info(f"Cache miss for key: {cache_key}")
        
        # Build query
        query = db.session.query(Book)
        
        # Apply search filter if provided
        if search:
            search_filter = f"%{search}%"
            query = query.filter(
                (Book.title.ilike(search_filter)) | 
                (Book.author.ilike(search_filter))
            )
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        books = query.offset(offset).limit(size).all()
        
        # Calculate total pages
        pages = math.ceil(total / size) if total > 0 else 1
        
        # Prepare response
        response = {
            "books": [book_to_dict(book) for book in books],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
        
        # Cache the result
        cache_service.set(cache_key, response)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        return jsonify({"error": "Failed to fetch books"}), 500

@app.route('/api/books', methods=['POST'])
def create_book():
    """Create a new book"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('title') or not data.get('author'):
            return jsonify({"error": "Title and author are required"}), 400
        
        # Check if book with same ISBN already exists
        if data.get('isbn'):
            existing_book = db.session.query(Book).filter(Book.isbn == data['isbn']).first()
            if existing_book:
                return jsonify({"error": f"Book with ISBN {data['isbn']} already exists"}), 400
        
        # Create new book
        book = Book(
            title=data['title'],
            author=data['author'],
            isbn=data.get('isbn'),
            description=data.get('description'),
            publication_year=data.get('publication_year')
        )
        
        db.session.add(book)
        db.session.commit()
        
        # Clear books cache
        cache_service.clear_pattern("books:*")
        
        logger.info(f"Created new book: {book.id}")
        return jsonify(book_to_dict(book)), 201
        
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create book"}), 500

@app.route('/api/books/<int:book_id>', methods=['GET'])
def get_book(book_id):
    """Get a specific book by ID"""
    try:
        book = db.session.get(Book, book_id)
        if not book:
            return jsonify({"error": f"Book with id {book_id} not found"}), 404
        
        return jsonify(book_to_dict(book))
        
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {e}")
        return jsonify({"error": "Failed to fetch book"}), 500

@app.route('/api/books/<int:book_id>/reviews', methods=['GET'])
def get_book_reviews(book_id):
    """Get all reviews for a specific book"""
    try:
        # Check if book exists
        book = db.session.get(Book, book_id)
        if not book:
            return jsonify({"error": f"Book with id {book_id} not found"}), 404
        
        page = int(request.args.get('page', 1))
        size = min(int(request.args.get('size', 10)), 100)
        rating_filter = request.args.get('rating_filter', type=float)
        
        # Create cache key
        cache_key = f"reviews:book:{book_id}:page:{page}:size:{size}:rating:{rating_filter or 'none'}"
        
        # Try cache first
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for reviews key: {cache_key}")
            return jsonify(cached_result)
        
        # Build query
        query = db.session.query(Review).filter(Review.book_id == book_id)
        
        # Apply rating filter if provided
        if rating_filter is not None:
            query = query.filter(Review.rating >= rating_filter)
        
        # Order by creation date (newest first)
        query = query.order_by(Review.created_at.desc())
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * size
        reviews = query.offset(offset).limit(size).all()
        
        # Calculate total pages
        pages = math.ceil(total / size) if total > 0 else 1
        
        # Prepare response
        response = {
            "reviews": [review_to_dict(review) for review in reviews],
            "total": total,
            "page": page,
            "size": size,
            "pages": pages
        }
        
        # Cache the result
        cache_service.set(cache_key, response)
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error fetching reviews for book {book_id}: {e}")
        return jsonify({"error": "Failed to fetch reviews"}), 500

@app.route('/api/books/<int:book_id>/reviews', methods=['POST'])
def create_review(book_id):
    """Create a new review for a book"""
    try:
        # Check if book exists
        book = db.session.get(Book, book_id)
        if not book:
            return jsonify({"error": f"Book with id {book_id} not found"}), 404
        
        data = request.get_json()
        
        # Validate required fields
        if not data.get('reviewer_name') or not data.get('rating'):
            return jsonify({"error": "Reviewer name and rating are required"}), 400
        
        # Validate rating range
        rating = float(data['rating'])
        if not (1.0 <= rating <= 5.0):
            return jsonify({"error": "Rating must be between 1.0 and 5.0"}), 400
        
        # Create new review
        review = Review(
            book_id=book_id,
            reviewer_name=data['reviewer_name'],
            reviewer_email=data.get('reviewer_email'),
            rating=rating,
            review_text=data.get('review_text')
        )
        
        db.session.add(review)
        db.session.commit()
        
        # Clear reviews cache for this book
        cache_service.clear_pattern(f"reviews:book:{book_id}:*")
        
        logger.info(f"Created new review: {review.id} for book: {book_id}")
        return jsonify(review_to_dict(review)), 201
        
    except Exception as e:
        logger.error(f"Error creating review for book {book_id}: {e}")
        db.session.rollback()
        return jsonify({"error": "Failed to create review"}), 500

@app.route('/api/books/<int:book_id>/reviews/stats')
def get_review_stats(book_id):
    """Get review statistics for a book"""
    try:
        # Check if book exists
        book = db.session.get(Book, book_id)
        if not book:
            return jsonify({"error": f"Book with id {book_id} not found"}), 404
        
        # Try cache first
        cache_key = f"review_stats:book:{book_id}"
        cached_stats = cache_service.get(cache_key)
        if cached_stats:
            logger.info(f"Cache hit for review stats: {book_id}")
            return jsonify(cached_stats)
        
        # Calculate statistics
        from sqlalchemy import func
        stats = db.session.query(
            func.count(Review.id).label('total_reviews'),
            func.avg(Review.rating).label('average_rating'),
            func.min(Review.rating).label('min_rating'),
            func.max(Review.rating).label('max_rating')
        ).filter(Review.book_id == book_id).first()
        
        # Format response
        response = {
            "book_id": book_id,
            "total_reviews": stats.total_reviews or 0,
            "average_rating": round(float(stats.average_rating), 2) if stats.average_rating else 0.0,
            "min_rating": float(stats.min_rating) if stats.min_rating else 0.0,
            "max_rating": float(stats.max_rating) if stats.max_rating else 0.0
        }
        
        # Cache the result
        cache_service.set(cache_key, response, ttl=60)  # Shorter TTL for stats
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error getting review stats for book {book_id}: {e}")
        return jsonify({"error": "Failed to get review statistics"}), 500

def book_to_dict(book):
    """Convert Book model to dictionary"""
    return {
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "isbn": book.isbn,
        "description": book.description,
        "publication_year": book.publication_year,
        "created_at": book.created_at.isoformat() if book.created_at else None,
        "updated_at": book.updated_at.isoformat() if book.updated_at else None
    }

def review_to_dict(review):
    """Convert Review model to dictionary"""
    return {
        "id": review.id,
        "book_id": review.book_id,
        "reviewer_name": review.reviewer_name,
        "reviewer_email": review.reviewer_email,
        "rating": review.rating,
        "review_text": review.review_text,
        "created_at": review.created_at.isoformat() if review.created_at else None,
        "updated_at": review.updated_at.isoformat() if review.updated_at else None
    }

# Global exception handler
@app.errorhandler(Exception)
def handle_exception(e):
    logger.error(f"Unhandled exception: {e}")
    return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)