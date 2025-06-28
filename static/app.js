// Book Review API Dashboard JavaScript

class BookReviewApp {
    constructor() {
        this.baseURL = '/api';
        this.currentPage = 1;
        this.pageSize = 10;
        this.searchQuery = '';
        this.selectedBookId = null;
        this.books = [];
        this.reviews = [];
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.checkAPIStatus();
        this.loadBooks();
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('book-search');
        searchInput.addEventListener('input', this.debounce((e) => {
            this.searchQuery = e.target.value;
            this.currentPage = 1;
            this.loadBooks();
        }, 300));

        // Page size change
        document.getElementById('books-per-page').addEventListener('change', (e) => {
            this.pageSize = parseInt(e.target.value);
            this.currentPage = 1;
            this.loadBooks();
        });

        // Refresh button
        document.getElementById('refresh-books').addEventListener('click', () => {
            this.loadBooks();
        });

        // Add book form
        document.getElementById('save-book-btn').addEventListener('click', () => {
            this.saveBook();
        });

        // Add review form
        document.getElementById('save-review-btn').addEventListener('click', () => {
            this.saveReview();
        });

        // Rating slider
        const ratingSlider = document.getElementById('review-rating');
        const ratingDisplay = document.getElementById('rating-display');
        ratingSlider.addEventListener('input', (e) => {
            ratingDisplay.textContent = `${e.target.value} stars`;
        });

        // Form reset on modal close
        document.getElementById('addBookModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('add-book-form').reset();
        });

        document.getElementById('addReviewModal').addEventListener('hidden.bs.modal', () => {
            document.getElementById('add-review-form').reset();
            document.getElementById('rating-display').textContent = '5.0 stars';
        });
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    async checkAPIStatus() {
        const statusElement = document.getElementById('api-status');
        
        try {
            const response = await fetch(`${this.baseURL}/../health`);
            if (response.ok) {
                statusElement.innerHTML = `
                    <span class="status-indicator online"></span>
                    <span class="text-success">API is online and ready</span>
                `;
            } else {
                throw new Error('API not responding correctly');
            }
        } catch (error) {
            statusElement.innerHTML = `
                <span class="status-indicator offline"></span>
                <span class="text-danger">API is offline or unreachable</span>
            `;
        }
    }

    async loadBooks() {
        const container = document.getElementById('books-container');
        const pagination = document.getElementById('books-pagination');
        
        // Show loading state
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading books...</span>
                </div>
                <p class="mt-2 text-muted">Loading books...</p>
            </div>
        `;

        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                size: this.pageSize
            });

            if (this.searchQuery) {
                params.append('search', this.searchQuery);
            }

            const response = await fetch(`${this.baseURL}/books?${params}`);
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const data = await response.json();
            this.books = data.books;
            
            this.renderBooks(data);
            this.renderPagination(data);
            
        } catch (error) {
            console.error('Error loading books:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load books: ${error.message}
                </div>
            `;
            pagination.classList.add('d-none');
        }
    }

    renderBooks(data) {
        const container = document.getElementById('books-container');
        
        if (data.books.length === 0) {
            container.innerHTML = `
                <div class="empty-state">
                    <i class="fas fa-book-open"></i>
                    <h5>No books found</h5>
                    <p class="text-muted">
                        ${this.searchQuery ? 
                            `No books match your search "${this.searchQuery}"` : 
                            'Start by adding your first book!'
                        }
                    </p>
                    ${!this.searchQuery ? 
                        '<button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addBookModal">Add First Book</button>' : 
                        ''
                    }
                </div>
            `;
            return;
        }

        const booksHTML = data.books.map(book => `
            <div class="col">
                <div class="card book-card fade-in-up ${this.selectedBookId === book.id ? 'selected' : ''}" 
                     onclick="app.selectBook(${book.id})">
                    <div class="card-body">
                        <h6 class="card-title">${this.highlightSearch(book.title)}</h6>
                        <p class="card-text">
                            <small class="text-muted">by ${this.highlightSearch(book.author)}</small>
                        </p>
                        ${book.description ? `
                            <p class="card-text small">${book.description.substring(0, 100)}${book.description.length > 100 ? '...' : ''}</p>
                        ` : ''}
                        <div class="d-flex justify-content-between align-items-center">
                            <small class="text-muted">
                                ${book.publication_year ? book.publication_year : 'Unknown year'}
                            </small>
                            ${book.isbn ? `
                                <small class="text-muted">ISBN: ${book.isbn}</small>
                            ` : ''}
                        </div>
                        <div class="mt-2">
                            <button class="btn btn-sm btn-outline-primary me-2" onclick="event.stopPropagation(); app.loadReviews(${book.id})">
                                <i class="fas fa-star me-1"></i>
                                Reviews
                            </button>
                            <button class="btn btn-sm btn-outline-success" onclick="event.stopPropagation(); app.showAddReviewModal(${book.id})">
                                <i class="fas fa-plus me-1"></i>
                                Add Review
                            </button>
                        </div>
                    </div>
                </div>
            </div>
        `).join('');

        container.innerHTML = `
            <div class="row row-cols-1 row-cols-md-2 row-cols-lg-3 g-3">
                ${booksHTML}
            </div>
        `;
    }

    highlightSearch(text) {
        if (!this.searchQuery) return text;
        
        const regex = new RegExp(`(${this.searchQuery})`, 'gi');
        return text.replace(regex, '<span class="search-highlight">$1</span>');
    }

    renderPagination(data) {
        const pagination = document.getElementById('books-pagination');
        
        if (data.pages <= 1) {
            pagination.classList.add('d-none');
            return;
        }

        pagination.classList.remove('d-none');
        
        let paginationHTML = '';
        
        // Previous button
        paginationHTML += `
            <li class="page-item ${data.page === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="app.goToPage(${data.page - 1})">
                    <i class="fas fa-chevron-left"></i>
                </a>
            </li>
        `;

        // Page numbers
        const startPage = Math.max(1, data.page - 2);
        const endPage = Math.min(data.pages, data.page + 2);

        if (startPage > 1) {
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="app.goToPage(1)">1</a></li>`;
            if (startPage > 2) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
        }

        for (let i = startPage; i <= endPage; i++) {
            paginationHTML += `
                <li class="page-item ${i === data.page ? 'active' : ''}">
                    <a class="page-link" href="#" onclick="app.goToPage(${i})">${i}</a>
                </li>
            `;
        }

        if (endPage < data.pages) {
            if (endPage < data.pages - 1) {
                paginationHTML += `<li class="page-item disabled"><span class="page-link">...</span></li>`;
            }
            paginationHTML += `<li class="page-item"><a class="page-link" href="#" onclick="app.goToPage(${data.pages})">${data.pages}</a></li>`;
        }

        // Next button
        paginationHTML += `
            <li class="page-item ${data.page === data.pages ? 'disabled' : ''}">
                <a class="page-link" href="#" onclick="app.goToPage(${data.page + 1})">
                    <i class="fas fa-chevron-right"></i>
                </a>
            </li>
        `;

        pagination.querySelector('.pagination').innerHTML = paginationHTML;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadBooks();
    }

    selectBook(bookId) {
        this.selectedBookId = bookId;
        this.loadReviews(bookId);
        
        // Update visual selection
        document.querySelectorAll('.book-card').forEach(card => {
            card.classList.remove('selected');
        });
        document.querySelector(`[onclick="app.selectBook(${bookId})"]`).classList.add('selected');
    }

    async loadReviews(bookId) {
        const container = document.getElementById('reviews-container');
        
        // Show loading state
        container.innerHTML = `
            <div class="text-center p-4">
                <div class="spinner-border" role="status">
                    <span class="visually-hidden">Loading reviews...</span>
                </div>
                <p class="mt-2 text-muted">Loading reviews...</p>
            </div>
        `;

        try {
            const [reviewsResponse, statsResponse] = await Promise.all([
                fetch(`${this.baseURL}/books/${bookId}/reviews`),
                fetch(`${this.baseURL}/books/${bookId}/reviews/stats`)
            ]);

            if (!reviewsResponse.ok || !statsResponse.ok) {
                throw new Error('Failed to load review data');
            }

            const reviewsData = await reviewsResponse.json();
            const statsData = await statsResponse.json();

            this.renderReviews(reviewsData, statsData, bookId);
            
        } catch (error) {
            console.error('Error loading reviews:', error);
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Failed to load reviews: ${error.message}
                </div>
            `;
        }
    }

    renderReviews(reviewsData, statsData, bookId) {
        const container = document.getElementById('reviews-container');
        const book = this.books.find(b => b.id === bookId);
        
        let content = `
            <div class="d-flex justify-content-between align-items-center mb-3">
                <h6 class="mb-0">Reviews for "${book?.title || 'Selected Book'}"</h6>
                <button class="btn btn-success btn-sm" onclick="app.showAddReviewModal(${bookId})">
                    <i class="fas fa-plus me-1"></i>
                    Add Review
                </button>
            </div>
        `;

        // Statistics
        if (statsData.total_reviews > 0) {
            content += `
                <div class="book-stats">
                    <div class="row text-center">
                        <div class="col">
                            <div class="stat-item">
                                <div class="stat-value">${statsData.total_reviews}</div>
                                <div class="stat-label">Reviews</div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="stat-item">
                                <div class="stat-value">${statsData.average_rating}</div>
                                <div class="stat-label">Average Rating</div>
                            </div>
                        </div>
                        <div class="col">
                            <div class="stat-item">
                                <div class="stat-value">${this.renderStars(statsData.average_rating)}</div>
                                <div class="stat-label">Stars</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        }

        // Reviews list
        if (reviewsData.reviews.length === 0) {
            content += `
                <div class="empty-state">
                    <i class="fas fa-star"></i>
                    <h6>No reviews yet</h6>
                    <p class="text-muted">Be the first to review this book!</p>
                    <button class="btn btn-primary" onclick="app.showAddReviewModal(${bookId})">
                        Write First Review
                    </button>
                </div>
            `;
        } else {
            const reviewsHTML = reviewsData.reviews.map(review => `
                <div class="card review-card mb-3 fade-in-up">
                    <div class="card-body">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <h6 class="card-title mb-1">${review.reviewer_name}</h6>
                                <small class="text-muted">${new Date(review.created_at).toLocaleDateString()}</small>
                            </div>
                            <div class="rating-stars">
                                ${this.renderStars(review.rating)}
                                <span class="ms-1">(${review.rating})</span>
                            </div>
                        </div>
                        ${review.review_text ? `
                            <p class="card-text">${review.review_text}</p>
                        ` : ''}
                    </div>
                </div>
            `).join('');

            content += `<div class="reviews-list">${reviewsHTML}</div>`;
        }

        container.innerHTML = content;
    }

    renderStars(rating) {
        const fullStars = Math.floor(rating);
        const hasHalfStar = rating % 1 >= 0.5;
        const emptyStars = 5 - fullStars - (hasHalfStar ? 1 : 0);

        let starsHTML = '';
        
        for (let i = 0; i < fullStars; i++) {
            starsHTML += '<i class="fas fa-star"></i>';
        }
        
        if (hasHalfStar) {
            starsHTML += '<i class="fas fa-star-half-alt"></i>';
        }
        
        for (let i = 0; i < emptyStars; i++) {
            starsHTML += '<i class="far fa-star empty"></i>';
        }

        return starsHTML;
    }

    async saveBook() {
        const title = document.getElementById('book-title').value.trim();
        const author = document.getElementById('book-author').value.trim();
        const isbn = document.getElementById('book-isbn').value.trim();
        const year = document.getElementById('book-year').value;
        const description = document.getElementById('book-description').value.trim();

        if (!title || !author) {
            this.showToast('Error', 'Title and author are required fields', 'error');
            return;
        }

        const bookData = {
            title,
            author,
            ...(isbn && { isbn }),
            ...(year && { publication_year: parseInt(year) }),
            ...(description && { description })
        };

        try {
            const response = await fetch(`${this.baseURL}/books`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bookData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create book');
            }

            const newBook = await response.json();

            // Close modal and reset form
            const modal = bootstrap.Modal.getInstance(document.getElementById('addBookModal'));
            modal.hide();

            // Refresh books list
            this.loadBooks();

            this.showToast('Success', `Book "${newBook.title}" has been added successfully`, 'success');

        } catch (error) {
            console.error('Error saving book:', error);
            this.showToast('Error', error.message, 'error');
        }
    }

    showAddReviewModal(bookId) {
        const book = this.books.find(b => b.id === bookId);
        if (!book) {
            this.showToast('Error', 'Please select a book first', 'error');
            return;
        }

        document.getElementById('review-book-id').value = bookId;
        
        // Update modal title
        const modalTitle = document.querySelector('#addReviewModal .modal-title');
        modalTitle.innerHTML = `
            <i class="fas fa-star me-2"></i>
            Add Review for "${book.title}"
        `;

        const modal = new bootstrap.Modal(document.getElementById('addReviewModal'));
        modal.show();
    }

    async saveReview() {
        const bookId = document.getElementById('review-book-id').value;
        const reviewerName = document.getElementById('reviewer-name').value.trim();
        const reviewerEmail = document.getElementById('reviewer-email').value.trim();
        const rating = parseFloat(document.getElementById('review-rating').value);
        const reviewText = document.getElementById('review-text').value.trim();

        if (!reviewerName || !rating) {
            this.showToast('Error', 'Reviewer name and rating are required', 'error');
            return;
        }

        const reviewData = {
            reviewer_name: reviewerName,
            rating,
            ...(reviewerEmail && { reviewer_email: reviewerEmail }),
            ...(reviewText && { review_text: reviewText })
        };

        try {
            const response = await fetch(`${this.baseURL}/books/${bookId}/reviews`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reviewData)
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Failed to create review');
            }

            const newReview = await response.json();

            // Close modal
            const modal = bootstrap.Modal.getInstance(document.getElementById('addReviewModal'));
            modal.hide();

            // Refresh reviews for this book
            this.loadReviews(bookId);

            this.showToast('Success', 'Your review has been added successfully', 'success');

        } catch (error) {
            console.error('Error saving review:', error);
            this.showToast('Error', error.message, 'error');
        }
    }

    showToast(title, message, type = 'info') {
        const toast = document.getElementById('notification-toast');
        const toastTitle = document.getElementById('toast-title');
        const toastBody = document.getElementById('toast-body');
        const toastIcon = document.getElementById('toast-icon');

        // Set content
        toastTitle.textContent = title;
        toastBody.textContent = message;

        // Set icon and styling based on type
        toast.className = 'toast';
        switch (type) {
            case 'success':
                toastIcon.className = 'fas fa-check-circle me-2 text-success';
                toast.classList.add('toast-success');
                break;
            case 'error':
                toastIcon.className = 'fas fa-exclamation-circle me-2 text-danger';
                toast.classList.add('toast-error');
                break;
            default:
                toastIcon.className = 'fas fa-info-circle me-2 text-info';
                toast.classList.add('toast-info');
        }

        // Show toast
        const bsToast = new bootstrap.Toast(toast);
        bsToast.show();
    }
}

// Initialize the app when the page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new BookReviewApp();
});

// Global functions for onclick handlers
window.app = {
    selectBook: (bookId) => app.selectBook(bookId),
    loadReviews: (bookId) => app.loadReviews(bookId),
    showAddReviewModal: (bookId) => app.showAddReviewModal(bookId),
    goToPage: (page) => app.goToPage(page)
};
