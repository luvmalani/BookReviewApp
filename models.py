from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Index, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    author = Column(String(255), nullable=False, index=True)
    isbn = Column(String(20), unique=True, nullable=True, index=True)
    description = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
# Relationship to reviews
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Book(id={self.id}, title='{self.title}', author='{self.author}')>"

class Review(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    book_id = Column(Integer, ForeignKey("books.id"), nullable=False)
    reviewer_name = Column(String(255), nullable=False)
    reviewer_email = Column(String(255), nullable=True)
    rating = Column(Float, nullable=False)  # Rating from 1.0 to 5.0
    review_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationship to book
    book = relationship("Book", back_populates="reviews")
    
    # Index for optimized queries by book_id
    __table_args__ = (
        Index('idx_reviews_book_id', 'book_id'),
        Index('idx_reviews_rating', 'rating'),
        Index('idx_reviews_created_at', 'created_at'),
    )
    
    def __repr__(self):
        return f"<Review(id={self.id}, book_id={self.book_id}, rating={self.rating})>"
