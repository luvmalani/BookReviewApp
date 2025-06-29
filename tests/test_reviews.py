import pytest
from unittest.mock import patch
from models import Book, Review

@patch('routes.reviews.cache_service')
class TestReviews:
    
    def test_create_review_success(self, mock_cache, client, db_session, sample_book_data, sample_review_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        mock_cache.get.return_value = None

        response = client.post(f"/api/books/{book.id}/reviews", json=sample_review_data)
        
        assert response.status_code == 201
        data = response.json()
        assert data["reviewer_name"] == sample_review_data["reviewer_name"]
        assert data["rating"] == sample_review_data["rating"]
        assert data["book_id"] == book.id
        assert "id" in data
        assert "created_at" in data
    
    def test_create_review_invalid_book(self, mock_cache, client, sample_review_data):
        mock_cache.get.return_value = None

        response = client.post("/api/books/999/reviews", json=sample_review_data)
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_create_review_invalid_rating(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

        invalid_review = {
            "reviewer_name": "Test Reviewer",
            "rating": 6.0,
            "review_text": "Test review"
        }

        mock_cache.get.return_value = None

        response = client.post(f"/api/books/{book.id}/reviews", json=invalid_review)
        assert response.status_code == 422
    
    def test_get_book_reviews_empty(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

        mock_cache.get.return_value = None

        response = client.get(f"/api/books/{book.id}/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert data["reviews"] == []
        assert data["total"] == 0
    
    def test_get_book_reviews_with_data(self, mock_cache, client, db_session, sample_book_data, sample_review_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        review1 = Review(book_id=book.id, **sample_review_data)
        review2_data = sample_review_data.copy()
        review2_data["reviewer_name"] = "Another Reviewer"
        review2_data["rating"] = 3.0
        review2 = Review(book_id=book.id, **review2_data)

        db_session.add_all([review1, review2])
        db_session.commit()

        mock_cache.get.return_value = None

        response = client.get(f"/api/books/{book.id}/reviews")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 2
        assert data["total"] == 2
    
    def test_get_book_reviews_invalid_book(self, mock_cache, client):
        mock_cache.get.return_value = None

        response = client.get("/api/books/999/reviews")
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]
    
    def test_get_book_reviews_pagination(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        reviews = [
            Review(book_id=book.id, reviewer_name=f"Reviewer {i}", rating=4.0, review_text=f"Review {i}")
            for i in range(15)
        ]
        db_session.add_all(reviews)
        db_session.commit()

        mock_cache.get.return_value = None

        response = client.get(f"/api/books/{book.id}/reviews?page=1&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 10
        assert data["page"] == 1
        assert data["pages"] == 2

        response = client.get(f"/api/books/{book.id}/reviews?page=2&size=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 5
        assert data["page"] == 2
    
    def test_get_book_reviews_rating_filter(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        reviews = [
            Review(book_id=book.id, reviewer_name="Reviewer 1", rating=2.0, review_text="Poor"),
            Review(book_id=book.id, reviewer_name="Reviewer 2", rating=4.0, review_text="Good"),
            Review(book_id=book.id, reviewer_name="Reviewer 3", rating=5.0, review_text="Excellent")
        ]
        db_session.add_all(reviews)
        db_session.commit()

        mock_cache.get.return_value = None

        response = client.get(f"/api/books/{book.id}/reviews?rating_filter=4.0")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["reviews"]) == 2
        assert all(review["rating"] >= 4.0 for review in data["reviews"])
    
    def test_get_review_by_id(self, mock_cache, client, db_session, sample_book_data, sample_review_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

        review = Review(book_id=book.id, **sample_review_data)
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        mock_cache.get.return_value = None

        response = client.get(f"/api/reviews/{review.id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == review.id
    
    def test_get_review_not_found(self, mock_cache, client):
        mock_cache.get.return_value = None

        response = client.get("/api/reviews/999")
        
        assert response.status_code == 404
    
    def test_update_review(self, mock_cache, client, db_session, sample_book_data, sample_review_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

        review = Review(book_id=book.id, **sample_review_data)
        db_session.add(review)
        db_session.commit()
        db_session.refresh(review)

        mock_cache.get.return_value = None

        update_data = {"rating": 5.0, "review_text": "Updated review text"}
        response = client.put(f"/api/reviews/{review.id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5.0
        assert data["review_text"] == "Updated review text"
    
    def test_delete_review(self, mock_cache, client, db_session, sample_book_data, sample_review_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

        review = Review(book_id=book.id, **sample_review_data)
        db_session.add(review)
        db_session.commit()
        review_id = review.id

        mock_cache.get.return_value = None

        response = client.delete(f"/api/reviews/{review_id}")
        assert response.status_code == 204

        response = client.get(f"/api/reviews/{review_id}")
        assert response.status_code == 404
    
    def test_get_review_stats(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()
        db_session.refresh(book)

        reviews = [
            Review(book_id=book.id, reviewer_name="Reviewer 1", rating=3.0),
            Review(book_id=book.id, reviewer_name="Reviewer 2", rating=4.0),
            Review(book_id=book.id, reviewer_name="Reviewer 3", rating=5.0)
        ]
        db_session.add_all(reviews)
        db_session.commit()

        mock_cache.get.return_value = None

        response = client.get(f"/api/books/{book.id}/reviews/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["book_id"] == book.id
        assert data["total_reviews"] == 3
        assert data["average_rating"] == 4.0
        assert data["min_rating"] == 3.0
        assert data["max_rating"] == 5.0
    
    def test_get_review_stats_no_reviews(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

        # Optional: Clean any reviews if leaked
        db_session.query(Review).delete()
        db_session.commit()

        mock_cache.get.return_value = None

        response = client.get(f"/api/books/{book.id}/reviews/stats")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_reviews"] == 0
        assert data["average_rating"] == 0.0
        assert data["min_rating"] == 0.0
        assert data["max_rating"] == 0.0
    
    def test_reviews_cache_hit(self, mock_cache, client, db_session, sample_book_data):
        book = Book(**sample_book_data)
        db_session.add(book)
        db_session.commit()

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
