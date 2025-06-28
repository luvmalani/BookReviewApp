import pytest
import tempfile
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
from database import Base, get_db
from app import app
from cache import CacheService

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session")
def test_db():
    """Create test database tables"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session(test_db):
    """Create a fresh database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client(db_session):
    """Create a test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()

@pytest.fixture
def mock_cache():
    """Create a mock cache service for testing"""
    class MockCacheService:
        def __init__(self):
            self.data = {}
            self.is_available = True
        
        def get(self, key: str):
            return self.data.get(key)
        
        def set(self, key: str, value, ttl: int = None):
            self.data[key] = value
            return True
        
        def delete(self, key: str):
            self.data.pop(key, None)
            return True
        
        def clear_pattern(self, pattern: str):
            keys_to_delete = [k for k in self.data.keys() if pattern.replace('*', '') in k]
            for key in keys_to_delete:
                del self.data[key]
            return True
    
    return MockCacheService()

@pytest.fixture
def failed_cache():
    """Create a mock cache service that simulates failure"""
    class FailedCacheService:
        def __init__(self):
            self.is_available = False
        
        def get(self, key: str):
            return None
        
        def set(self, key: str, value, ttl: int = None):
            return False
        
        def delete(self, key: str):
            return False
        
        def clear_pattern(self, pattern: str):
            return False
    
    return FailedCacheService()

@pytest.fixture
def sample_book_data():
    """Sample book data for testing"""
    return {
        "title": "Test Book",
        "author": "Test Author",
        "isbn": "1234567890123",
        "description": "A test book for unit testing",
        "publication_year": 2023
    }

@pytest.fixture
def sample_review_data():
    """Sample review data for testing"""
    return {
        "reviewer_name": "Test Reviewer",
        "reviewer_email": "test@example.com",
        "rating": 4.5,
        "review_text": "This is a great test book!"
    }
