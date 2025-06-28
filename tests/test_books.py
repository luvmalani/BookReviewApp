import pytest
from unittest.mock import patch
from models import Book
from schemas import BookCreate

class TestBooks:
    
    def test_create_book_success(self, client, sample_book_data):
        """Test successful book creation"""
        response = client.post("/api/books", json=sample_book_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == sample_book_data["title"]
        assert data["author"] == sample_book_data["author"]
        assert data["isbn"] == sample_book_data["isbn"]
        assert "id" in data
        assert "created_at" in data
    
    def test_create_book_duplicate_isbn(self, client, sample_book_data, db_session):
        """Test creating book with duplicate ISBN fails"""
        # Create first book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        # Try to create another book with same ISBN
        response = client.post("/api/books", json=sample_book_data)
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_create_book_invalid_data(self, client):
        """Test creating book with invalid data"""
        invalid_data = {
            "title": "",  # Empty title should fail
            "author": "Test Author"
        }
        
        response = client.post("/api/books", json=invalid_data)
        assert response.status_code == 422
    
    def test_get_books_empty(self, client):
        """Test getting books when database is empty"""
        response = client.get("/api/books")
        
        assert response.status_code == 200
        data = response.json()
        assert data["books"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["size"] == 10
    
    def test_get_books_with_data(self, client, db_session, sample_book_data):
        """Test getting books with data in database"""
        # Create test books
        book1 = Book(**sample_book_data)
        book2_data = sample_book_data.copy()
        book2_data["title"] = "Another Test Book"
        book2_data["isbn"] = "9876543210987"
        book2 = Book(**book2_data)
        
        db_session.add_all([book1, book2])
        db_session.commit()
        
        response = client.get("/api/books")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 2
        assert data["total"] == 2
    
    def test_get_books_pagination(self, client, db_session):
        """Test book pagination"""
        # Create 15 test books
        books = []
        for i in range(15):
            book_data = {
                "title": f"Test Book {i}",
                "author": f"Author {i}",
                "isbn": f"123456789012{i:01d}"
            }
            books.append(Book(**book_data))
        
        db_session.add_all(books)
        db_session.commit()
        
        # Test first page
        response = client.get("/api/books?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 10
        assert data["page"] == 1
        assert data["pages"] == 2
        
        # Test second page
        response = client.get("/api/books?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 5
        assert data["page"] == 2
    
    def test_get_books_search(self, client, db_session):
        """Test book search functionality"""
        # Create test books
        books = [
            Book(title="Python Programming", author="John Doe", isbn="1111111111111"),
            Book(title="Java Fundamentals", author="Jane Smith", isbn="2222222222222"),
            Book(title="Advanced Python", author="Bob Johnson", isbn="3333333333333")
        ]
        db_session.add_all(books)
        db_session.commit()
        
        # Search by title
        response = client.get("/api/books?search=Python")
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 2
        
        # Search by author
        response = client.get("/api/books?search=Jane")
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 1
        assert data["books"][0]["author"] == "Jane Smith"
    
    def test_get_book_by_id(self, client, db_session, sample_book_data):
        """Test getting a specific book by ID"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        response = client.get(f"/api/books/{book.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == book.id
        assert data["title"] == sample_book_data["title"]
    
    def test_get_book_not_found(self, client):
        """Test getting non-existent book"""
        response = client.get("/api/books/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_book(self, client, db_session, sample_book_data):
        """Test updating a book"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        update_data = {"title": "Updated Title"}
        response = client.put(f"/api/books/{book.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["author"] == sample_book_data["author"]  # Unchanged
    
    def test_delete_book(self, client, db_session, sample_book_data):
        """Test deleting a book"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        book_id = book.id
        
        response = client.delete(f"/api/books/{book_id}")
        
        assert response.status_code == 204
        
        # Verify book is deleted
        response = client.get(f"/api/books/{book_id}")
        assert response.status_code == 404
    
    @patch('routes.books.cache_service')
    def test_cache_hit_scenario(self, mock_cache, client, sample_book_data):
        """Test cache hit scenario for get_books"""
        # Setup mock cache to return data
        cached_response = {
            "books": [sample_book_data],
            "total": 1,
            "page": 1,
            "size": 10,
            "pages": 1
        }
        mock_cache.get.return_value = cached_response
        
        response = client.get("/api/books")
        
        assert response.status_code == 200
        assert response.json() == cached_response
        mock_cache.get.assert_called_once()
    
    @patch('routes.books.cache_service')
    def test_cache_miss_scenario(self, mock_cache, client, db_session, sample_book_data):
        """Test cache miss scenario - should fetch from database and cache result"""
        # Setup mock cache to return None (cache miss)
        mock_cache.get.return_value = None
        mock_cache.set.return_value = True
        
        # Create book in database
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get("/api/books")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["books"]) == 1
        
        # Verify cache was called
        mock_cache.get.assert_called_once()
        mock_cache.set.assert_called_once()
