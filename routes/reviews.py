import logging
import math
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from models import Book, Review
from schemas import (
    Review as ReviewSchema,
    ReviewCreate,
    ReviewUpdate,
    ReviewListResponse,
    ErrorResponse
)
from cache import cache_service

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/books/{book_id}/reviews", response_model=ReviewListResponse)
async def get_book_reviews(
    book_id: int,
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(10, ge=1, le=100, description="Page size"),
    rating_filter: Optional[float] = Query(None, ge=1.0, le=5.0, description="Filter by minimum rating"),
    db: Session = Depends(get_db)
):
    """
    Get all reviews for a specific book with pagination and optional rating filter
    """
    try:
        # Check if book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        # Create cache key
        cache_key = f"reviews:book:{book_id}:page:{page}:size:{size}:rating:{rating_filter or 'none'}"
        
        # Try cache first
        cached_result = cache_service.get(cache_key)
        if cached_result:
            logger.info(f"Cache hit for reviews key: {cache_key}")
            return cached_result
        
        logger.info(f"Cache miss for reviews key: {cache_key}")
        
        # Build query
        query = db.query(Review).filter(Review.book_id == book_id)
        
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
        response = ReviewListResponse(
            reviews=[ReviewSchema.from_orm(review) for review in reviews],
            total=total,
            page=page,
            size=size,
            pages=pages
        )
        
        # Cache the result
        cache_service.set(cache_key, response.dict())
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching reviews for book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch reviews"
        )

@router.get("/reviews/{review_id}", response_model=ReviewSchema)
async def get_review(review_id: int, db: Session = Depends(get_db)):
    """Get a specific review by ID"""
    try:
        # Try cache first
        cache_key = f"review:{review_id}"
        cached_review = cache_service.get(cache_key)
        if cached_review:
            logger.info(f"Cache hit for review: {review_id}")
            return cached_review
        
        # Query database
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )
        
        # Convert to schema and cache
        review_data = ReviewSchema.from_orm(review)
        cache_service.set(cache_key, review_data.dict())
        
        return review_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching review {review_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch review"
        )

@router.post("/books/{book_id}/reviews", response_model=ReviewSchema, status_code=status.HTTP_201_CREATED)
async def create_review(
    book_id: int,
    review_data: ReviewCreate,
    db: Session = Depends(get_db)
):
    """Create a new review for a book"""
    try:
        # Check if book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        # Create new review
        db_review = Review(book_id=book_id, **review_data.dict())
        db.add(db_review)
        db.commit()
        db.refresh(db_review)
        
        # Clear reviews cache for this book
        cache_service.clear_pattern(f"reviews:book:{book_id}:*")
        
        logger.info(f"Created new review: {db_review.id} for book: {book_id}")
        return ReviewSchema.from_orm(db_review)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating review for book {book_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create review"
        )

@router.put("/reviews/{review_id}", response_model=ReviewSchema)
async def update_review(
    review_id: int,
    review_update: ReviewUpdate,
    db: Session = Depends(get_db)
):
    """Update a review"""
    try:
        # Find review
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )
        
        # Update fields
        update_data = review_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(review, field, value)
        
        db.commit()
        db.refresh(review)
        
        # Clear caches
        cache_service.delete(f"review:{review_id}")
        cache_service.clear_pattern(f"reviews:book:{review.book_id}:*")
        
        logger.info(f"Updated review: {review_id}")
        return ReviewSchema.from_orm(review)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating review {review_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update review"
        )

@router.delete("/reviews/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_review(review_id: int, db: Session = Depends(get_db)):
    """Delete a review"""
    try:
        review = db.query(Review).filter(Review.id == review_id).first()
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Review with id {review_id} not found"
            )
        
        book_id = review.book_id
        db.delete(review)
        db.commit()
        
        # Clear caches
        cache_service.delete(f"review:{review_id}")
        cache_service.clear_pattern(f"reviews:book:{book_id}:*")
        
        logger.info(f"Deleted review: {review_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting review {review_id}: {e}")
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete review"
        )

@router.get("/books/{book_id}/reviews/stats")
async def get_review_stats(book_id: int, db: Session = Depends(get_db)):
    """Get review statistics for a book"""
    try:
        # Check if book exists
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Book with id {book_id} not found"
            )
        
        # Try cache first
        cache_key = f"review_stats:book:{book_id}"
        cached_stats = cache_service.get(cache_key)
        if cached_stats:
            logger.info(f"Cache hit for review stats: {book_id}")
            return cached_stats
        
        # Calculate statistics
        stats = db.query(
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
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting review stats for book {book_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get review statistics"
        )
