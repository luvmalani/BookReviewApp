import logging
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Book, Review
from schemas import (
    Book as BookSchema, 
    BookCreate, 
    BookUpdate, 
    BookListResponse,
    ErrorResponse
)
from cache import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/books", response_model=BookListResponse)
async def get_books(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    search: Optional[str] = Query(None, description="Search in title or author"),
    db: Session = Depends(get_db)
):
    """
    Get all books with pagination and optional search
    Implements cache-first strategy
    """
    try:
        # Create cache key
        cache_key = f"books:page:{page}:size:{size}:search:{search or 'none'}"
        
        # Try to get from cache first
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for key: {cache_key}")
            return cached_result
        
        logger.info(f"Cache miss for key: {cache_key}")
        
        # Build query
        query = db.query(Book)
        
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
        response = BookListResponse(
            books=[BookSchema.from_orm(book) for book in books],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
        # Cache the result
        cache_service.set(cache_key, response.dict())
        
        return response
        
    except Exception as e:
        logger.error(f"Error fetching books: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch books"
        )

@router.get("/books/{book_id}", response_model=BookSchema)
async def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get a specific book by ID"""
    try:
        # Try cache first
        cache_key = f"book:{book_id}"
        cached_book = cache_service.get(cache_key)
        if cached_book:
            logger.info(f"Cache hit for book: {book_id}")
            return cached_book
        
        # Query database
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        # Convert to schema and cache
        book_data = BookSchema.from_orm(book)
        cache_service.set(cache_key, book_data.dict())
        
        return book_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch book"
        )

@router.post("/books", response_model=BookSchema, status_code=status.HTTP_201_CREATED)
async def create_book(book_data: BookCreate, db: Session = Depends(get_db)):
    """Create a new book"""
    try:
        # Check if book with same ISBN already exists
        if book_data.isbn:
            existing_book = db.query(Book).filter(Book.isbn == book_data.isbn).first()
            if existing_book:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Book with ISBN {book_data.isbn} already exists"
                )
        
        # Create new book
        db_book = Book(**book_data.dict())
        db.add(db_book)
        db.commit()
        db.refresh(db_book)
        
        # Clear books cache
        cache_service.clear_pattern("books:*")
        
        logger.info(f"Created new book: {db_book.id}")
        return BookSchema.from_orm(db_book)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating book: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create book"
        )

@router.put("/books/{book_id}", response_model=BookSchema)
async def update_book(
    book_id: int, 
    book_update: BookUpdate, 
    db: Session = Depends(get_db)
):
    """Update a book"""
    try:
        # Find book
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        # Check ISBN uniqueness if being updated
        if book_update.isbn and book_update.isbn != book.isbn:
            existing_book = db.query(Book).filter(Book.isbn == book_update.isbn).first()
            if existing_book:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Book with ISBN {book_update.isbn} already exists"
                )
        
        # Update fields
        update_data = book_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(book, field, value)
        
        db.commit()
        db.refresh(book)
        
        # Clear caches
        cache_service.delete(f"book:{book_id}")
        cache_service.clear_pattern("books:*")
        
        logger.info(f"Updated book: {book_id}")
        return BookSchema.from_orm(book)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating book {book_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update book"
        )

@router.delete("/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book(book_id: int, db: Session = Depends(get_db)):
    """Delete a book"""
    try:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        db.delete(book)
        db.commit()
        
        # Clear caches
        cache_service.delete(f"book:{book_id}")
        cache_service.clear_pattern("books:*")
        cache_service.clear_pattern(f"reviews:book:{book_id}:*")
        
        logger.info(f"Deleted book: {book_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting book {book_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete book"
        )
