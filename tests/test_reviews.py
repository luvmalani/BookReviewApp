import pytest
from unittest.mock import patch
from models import Book, Review

class TestReviews:
    
    def test_create_review_success(self, client, db_session, sample_book_data, sample_review_data):
        """Test successful review creation"""
        # Create a book first
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        response = client.post(f"/api/books/{book.id}/reviews", json=sample_review_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["reviewer_name"] == sample_review_data["reviewer_name"]
        assert data["rating"] == sample_review_data["rating"]
        assert data["book_id"] == book.id
        assert "id" in data
        assert "created_at" in data
    
    def test_create_review_invalid_book(self, client, sample_review_data):
        """Test creating review for non-existent book"""
        response = client.post("/api/books/999/reviews", json=sample_review_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_review_invalid_rating(self, client, db_session, sample_book_data):
        """Test creating review with invalid rating"""
        # Create a book first
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        invalid_review = {
            "reviewer_name": "Test Reviewer",
            "rating": 6.0,  # Invalid rating > 5.0
            "review_text": "Test review"
        }
        
        response = client.post(f"/api/books/{book.id}/reviews", json=invalid_review)
        assert response.status_code == 422
    
    def test_get_book_reviews_empty(self, client, db_session, sample_book_data):
        """Test getting reviews for book with no reviews"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get(f"/api/books/{book.id}/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert data["reviews"] == []
        assert data["total"] == 0
    
    def test_get_book_reviews_with_data(self, client, db_session, sample_book_data, sample_review_data):
        """Test getting reviews with data"""
        # Create book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        # Create reviews
        review1 = Review(book_id=book.id, **sample_review_data)
        review2_data = sample_review_data.copy()
        review2_data["reviewer_name"] = "Another Reviewer"
        review2_data["rating"] = 3.0
        review2 = Review(book_id=book.id, **review2_data)
        
        db_session.add_all([review1, review2])
        db_session.commit()
        
        response = client.get(f"/api/books/{book.id}/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 2
        assert data["total"] == 2
    
    def test_get_book_reviews_invalid_book(self, client):
        """Test getting reviews for non-existent book"""
        response = client.get("/api/books/999/reviews")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_book_reviews_pagination(self, client, db_session, sample_book_data):
        """Test review pagination"""
        # Create book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        # Create 15 reviews
        reviews = []
        for i in range(15):
            review = Review(
                book_id=book.id,
                reviewer_name=f"Reviewer {i}",
                rating=4.0,
                review_text=f"Review {i}"
            )
            reviews.append(review)
        
        db_session.add_all(reviews)
        db_session.commit()
        
        # Test first page
        response = client.get(f"/api/books/{book.id}/reviews?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 10
        assert data["page"] == 1
        assert data["pages"] == 2
        
        # Test second page
        response = client.get(f"/api/books/{book.id}/reviews?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 5
        assert data["page"] == 2
    
    def test_get_book_reviews_rating_filter(self, client, db_session, sample_book_data):
        """Test filtering reviews by minimum rating"""
        # Create book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        # Create reviews with different ratings
        reviews = [
            Review(book_id=book.id, reviewer_name="Reviewer 1", rating=2.0, review_text="Poor"),
            Review(book_id=book.id, reviewer_name="Reviewer 2", rating=4.0, review_text="Good"),
            Review(book_id=book.id, reviewer_name="Reviewer 3", rating=5.0, review_text="Excellent")
        ]
        db_session.add_all(reviews)
        db_session.commit()
        
        # Filter by minimum rating 4.0
        response = client.get(f"/api/books/{book.id}/reviews?rating_filter=4.0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 2  # Only ratings 4.0 and 5.0
        assert all(review["rating"] >= 4.0 for review in data["reviews"])
    
    def test_get_review_by_id(self, client, db_session, sample_book_data, sample_review_data):
        """Test getting specific review by ID"""
        # Create book and review
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        review = Review(book_id=book.id, **sample_review_data)
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        response = client.get(f"/api/reviews/{review.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review.id
        assert data["reviewer_name"] == sample_review_data["reviewer_name"]
    
    def test_get_review_not_found(self, client):
        """Test getting non-existent review"""
        response = client.get("/api/reviews/999")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_update_review(self, client, db_session, sample_book_data, sample_review_data):
        """Test updating a review"""
        # Create book and review
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        review = Review(book_id=book.id, **sample_review_data)
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)
        
        update_data = {"rating": 5.0, "review_text": "Updated review text"}
        response = client.put(f"/api/reviews/{review.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5.0
        assert data["review_text"] == "Updated review text"
        assert data["reviewer_name"] == sample_review_data["reviewer_name"]  # Unchanged
    
    def test_delete_review(self, client, db_session, sample_book_data, sample_review_data):
        """Test deleting a review"""
        # Create book and review
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        review = Review(book_id=book.id, **sample_review_data)
        db_session.add(review)
        db_session.commit()
        review_id = review.id
        
        response = client.delete(f"/api/reviews/{review_id}")
        
        assert response.status_code == 204
        
        # Verify review is deleted
        response = client.get(f"/api/reviews/{review_id}")
        assert response.status_code == 404
    
    def test_get_review_stats(self, client, db_session, sample_book_data):
        """Test getting review statistics for a book"""
        # Create book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)
        
        # Create reviews with different ratings
        reviews = [
            Review(book_id=book.id, reviewer_name="Reviewer 1", rating=3.0),
            Review(book_id=book.id, reviewer_name="Reviewer 2", rating=4.0),
            Review(book_id=book.id, reviewer_name="Reviewer 3", rating=5.0)
        ]
        db_session.add_all(reviews)
        db_session.commit()
        
        response = client.get(f"/api/books/{book.id}/reviews/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book.id
        assert data["total_reviews"] == 3
        assert data["average_rating"] == 4.0
        assert data["min_rating"] == 3.0
        assert data["max_rating"] == 5.0
    
    def test_get_review_stats_no_reviews(self, client, db_session, sample_book_data):
        """Test getting review stats for book with no reviews"""
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        response = client.get(f"/api/books/{book.id}/reviews/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_reviews"] == 0
        assert data["average_rating"] == 0.0
        assert data["min_rating"] == 0.0
        assert data["max_rating"] == 0.0
    
    @patch('routes.reviews.cache_service')
    def test_reviews_cache_hit(self, mock_cache, client, db_session, sample_book_data):
        """Test cache hit scenario for get_book_reviews"""
        # Create book
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        
        # Setup mock cache
        cached_response = {
            "reviews": [],
            "total": 0,
            "page": 1,
            "size": 10,
            "pages": 1
        }
        mock_cache.get.return_value = cached_response
        
        response = client.get(f"/api/books/{book.id}/reviews")
        
        assert response.status_code == 200
        assert response.json() == cached_response
        mock_cache.get.assert_called_once()
