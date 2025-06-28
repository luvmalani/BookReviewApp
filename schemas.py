from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator

# Book schemas
class BookBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    author: str = Field(..., min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=2030)

class BookCreate(BookBase):
    pass

class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    author: Optional[str] = Field(None, min_length=1, max_length=255)
    isbn: Optional[str] = Field(None, max_length=20)
    description: Optional[str] = None
    publication_year: Optional[int] = Field(None, ge=1000, le=2030)

class Book(BookBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BookWithReviews(Book):
    reviews: List['Review'] = []

# Review schemas
class ReviewBase(BaseModel):
    reviewer_name: str = Field(..., min_length=1, max_length=255)
    reviewer_email: Optional[EmailStr] = None
    rating: float = Field(..., ge=1.0, le=5.0)
    review_text: Optional[str] = None

class ReviewCreate(ReviewBase):
    @validator('rating')
    def validate_rating(cls, v):
        if not (1.0 <= v <= 5.0):
            raise ValueError('Rating must be between 1.0 and 5.0')
        return round(v, 1)

class ReviewUpdate(BaseModel):
    reviewer_name: Optional[str] = Field(None, min_length=1, max_length=255)
    reviewer_email: Optional[EmailStr] = None
    rating: Optional[float] = Field(None, ge=1.0, le=5.0)
    review_text: Optional[str] = None
    
    @validator('rating')
    def validate_rating(cls, v):
        if v is not None and not (1.0 <= v <= 5.0):
            raise ValueError('Rating must be between 1.0 and 5.0')
        return round(v, 1) if v is not None else v

class Review(ReviewBase):
    id: int
    book_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ReviewWithBook(Review):
    book: Book

# Pagination schemas
class PaginationParams(BaseModel):
    page: int = Field(1, ge=1)
    size: int = Field(10, ge=1, le=100)

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int

# Response schemas
class BookListResponse(BaseModel):
    books: List[Book]
    total: int
    page: int
    size: int
    pages: int

class ReviewListResponse(BaseModel):
    reviews: List[Review]
    total: int
    page: int
    size: int
    pages: int

# Error schemas
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

# Update forward references
BookWithReviews.model_rebuild()
ReviewWithBook.model_rebuild()
