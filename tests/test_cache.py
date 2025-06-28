import pytest
from unittest.mock import patch, MagicMock
from cache import CacheService

class TestCacheService:
    
    def test_cache_init_success(self):
        """Test successful cache initialization"""
        with patch('redis.from_url') as mock_redis:
            mock_client = MagicMock()
            mock_redis.return_value = mock_client
            mock_client.ping.return_value = True
            
            cache = CacheService()
            
            assert cache.is_available is True
            assert cache.redis_client == mock_client
            mock_client.ping.assert_called_once()
    
    def test_cache_init_failure(self):
        """Test cache initialization failure"""
        with patch('redis.from_url') as mock_redis:
            mock_redis.side_effect = Exception("Connection failed")
            
            cache = CacheService()
            
            assert cache.is_available is False
            assert cache.redis_client is None
    
    def test_cache_get_success(self, mock_cache):
        """Test successful cache get"""
        test_data = {"key": "value"}
        mock_cache.set("test_key", test_data)
        
        result = mock_cache.get("test_key")
        
        assert result == test_data
    
    def test_cache_get_miss(self, mock_cache):
        """Test cache miss"""
        result = mock_cache.get("nonexistent_key")
        
        assert result is None
    
    def test_cache_get_unavailable(self, failed_cache):
        """Test cache get when cache is unavailable"""
        result = failed_cache.get("test_key")
        
        assert result is None
    
    def test_cache_set_success(self, mock_cache):
        """Test successful cache set"""
        test_data = {"key": "value"}
        
        result = mock_cache.set("test_key", test_data)
        
        assert result is True
        assert mock_cache.get("test_key") == test_data
    
    def test_cache_set_unavailable(self, failed_cache):
        """Test cache set when cache is unavailable"""
        result = failed_cache.set("test_key", {"key": "value"})
        
        assert result is False
    
    def test_cache_delete_success(self, mock_cache):
        """Test successful cache delete"""
        mock_cache.set("test_key", {"key": "value"})
        
        result = mock_cache.delete("test_key")
        
        assert result is True
        assert mock_cache.get("test_key") is None
    
    def test_cache_delete_unavailable(self, failed_cache):
        """Test cache delete when cache is unavailable"""
        result = failed_cache.delete("test_key")
        
        assert result is False
    
    def test_cache_clear_pattern_success(self, mock_cache):
        """Test successful pattern clearing"""
        mock_cache.set("books:1", {"id": 1})
        mock_cache.set("books:2", {"id": 2})
        mock_cache.set("reviews:1", {"id": 1})
        
        result = mock_cache.clear_pattern("books:*")
        
        assert result is True
        assert mock_cache.get("books:1") is None
        assert mock_cache.get("books:2") is None
        assert mock_cache.get("reviews:1") is not None  # Should remain
    
    def test_cache_clear_pattern_unavailable(self, failed_cache):
        """Test pattern clearing when cache is unavailable"""
        result = failed_cache.clear_pattern("books:*")
        
        assert result is False
    
    def test_integration_cache_fallback(self, client, db_session, sample_book_data):
        """Integration test: Verify API works when cache is down"""
        # This test verifies the cache fallback behavior
        with patch('routes.books.cache_service') as mock_cache:
            # Simulate cache being unavailable
            mock_cache.get.return_value = None
            mock_cache.set.return_value = False
            mock_cache.is_available = False
            
            # Create book in database
            from models import Book
            book = Book(**sample_book_data)
            db_session.add(book)
            db_session.commit()
            
            # API should still work without cache
            response = client.get("/api/books")
            
            assert response.status_code == 200
            data = response.json()
            assert len(data["books"]) == 1
            assert data["books"][0]["title"] == sample_book_data["title"]
            
            # Verify cache was attempted but gracefully handled failure
            mock_cache.get.assert_called()
            mock_cache.set.assert_called()
    
    def test_real_cache_service_error_handling(self):
        """Test real CacheService error handling"""
        # Test with invalid Redis URL to trigger connection error
        with patch('cache.settings') as mock_settings:
            mock_settings.redis_url = "redis://invalid-host:6379/0"
            
            cache = CacheService()
            
            # Should handle connection failure gracefully
            assert cache.is_available is False
            assert cache.get("test") is None
            assert cache.set("test", "value") is False
