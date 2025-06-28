// Simple Book Review System JavaScript
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
        this.loadBooks();
    }

    setupEventListeners() {
        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', this.debounce((e) => {
                this.searchQuery = e.target.value;
                this.currentPage = 1;
                this.loadBooks();
            }, 500));
        }

        // Forms
        const bookForm = document.getElementById('bookForm');
        if (bookForm) {
            bookForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveBook();
            });
        }

        const reviewForm = document.getElementById('reviewForm');
        if (reviewForm) {
            reviewForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.saveReview();
            });
        }
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



    async loadBooks() {
        const container = document.getElementById('books-container');
        container.innerHTML = '<div class="empty-message">Loading books...</div>';
        
        try {
            const params = new URLSearchParams({
                page: this.currentPage,
                size: this.pageSize
            });
            
            if (this.searchQuery) {
                params.append('search', this.searchQuery);
            }
            
            const response = await fetch(`${this.baseURL}/books?${params}`);
            const data = await response.json();
            
            if (response.ok) {
                this.books = data.books;
                this.renderBooks(data);
                this.renderPagination(data, 'books-pagination');
            } else {
                container.innerHTML = `<div class="empty-message">Error: ${data.error || 'Failed to load books'}</div>`;
            }
        } catch (error) {
            container.innerHTML = '<div class="empty-message">Failed to connect to API</div>';
        }
    }

    renderBooks(data) {
        const container = document.getElementById('books-container');
        
        if (!data.books || data.books.length === 0) {
            container.innerHTML = '<div class="empty-message">No books found. Add some books to get started!</div>';
            return;
        }
        
        let html = '';
        data.books.forEach(book => {
            const selectedClass = this.selectedBookId === book.id ? 'selected' : '';
            html += `
                <div class="book-item ${selectedClass}" onclick="app.selectBook(${book.id})">
                    <div class="book-title">${this.escapeHtml(book.title)}</div>
                    <div class="book-author">by ${this.escapeHtml(book.author)}</div>
                    ${book.publication_year ? `<div style="font-size: 12px; color: #999;">Published: ${book.publication_year}</div>` : ''}
                    ${book.isbn ? `<div style="font-size: 12px; color: #999;">ISBN: ${book.isbn}</div>` : ''}
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    renderPagination(data, containerId) {
        const container = document.getElementById(containerId);
        if (!container || data.pages <= 1) {
            container.innerHTML = '';
            return;
        }
        
        let html = '';
        
        // Previous button
        if (data.page > 1) {
            html += `<button onclick="app.goToPage(${data.page - 1})">&lt; Prev</button>`;
        }
        
        // Page numbers
        for (let i = 1; i <= data.pages; i++) {
            if (i === data.page) {
                html += `<button class="active">${i}</button>`;
            } else {
                html += `<button onclick="app.goToPage(${i})">${i}</button>`;
            }
        }
        
        // Next button
        if (data.page < data.pages) {
            html += `<button onclick="app.goToPage(${data.page + 1})">Next &gt;</button>`;
        }
        
        container.innerHTML = html;
    }

    goToPage(page) {
        this.currentPage = page;
        this.loadBooks();
    }

    selectBook(bookId) {
        this.selectedBookId = bookId;
        const book = this.books.find(b => b.id === bookId);
        
        // Update UI
        document.querySelectorAll('.book-item').forEach(item => {
            item.classList.remove('selected');
        });
        event.target.closest('.book-item').classList.add('selected');
        
        // Show book info
        const infoDiv = document.getElementById('selected-book-info');
        infoDiv.innerHTML = `
            <div style="border: 1px solid #ddd; padding: 10px; margin-bottom: 10px; background: #f9f9f9;">
                <strong>${this.escapeHtml(book.title)}</strong><br>
                <em>by ${this.escapeHtml(book.author)}</em>
                ${book.description ? `<br><br>${this.escapeHtml(book.description)}` : ''}
            </div>
        `;
        
        // Show stats section
        document.getElementById('book-stats').style.display = 'block';
        
        // Load reviews and stats
        this.loadReviews(bookId);
        this.loadReviewStats(bookId);
    }

    async loadReviews(bookId) {
        const container = document.getElementById('reviews-container');
        container.innerHTML = '<div class="empty-message">Loading reviews...</div>';
        
        try {
            const response = await fetch(`${this.baseURL}/books/${bookId}/reviews`);
            const data = await response.json();
            
            if (response.ok) {
                this.reviews = data.reviews;
                this.renderReviews(data);
            } else {
                container.innerHTML = `<div class="empty-message">Error: ${data.error || 'Failed to load reviews'}</div>`;
            }
        } catch (error) {
            container.innerHTML = '<div class="empty-message">Failed to load reviews</div>';
        }
    }

    async loadReviewStats(bookId) {
        try {
            const response = await fetch(`${this.baseURL}/books/${bookId}/reviews/stats`);
            const data = await response.json();
            
            if (response.ok) {
                document.getElementById('total-reviews').textContent = data.total_reviews;
                document.getElementById('avg-rating').textContent = data.average_rating ? data.average_rating.toFixed(1) : '0';
                document.getElementById('min-rating').textContent = data.min_rating || '0';
                document.getElementById('max-rating').textContent = data.max_rating || '0';
            }
        } catch (error) {
            console.error('Failed to load review stats:', error);
        }
    }

    renderReviews(data) {
        const container = document.getElementById('reviews-container');
        
        if (!data.reviews || data.reviews.length === 0) {
            container.innerHTML = '<div class="empty-message">No reviews yet. Be the first to review this book!</div>';
            return;
        }
        
        let html = '';
        data.reviews.forEach(review => {
            const stars = '⭐'.repeat(Math.floor(review.rating));
            html += `
                <div class="review-item">
                    <div class="reviewer-name">${this.escapeHtml(review.reviewer_name)}</div>
                    <div class="rating">${stars} ${review.rating}/5</div>
                    ${review.review_text ? `<div class="review-text">${this.escapeHtml(review.review_text)}</div>` : ''}
                    <div style="font-size: 12px; color: #999; margin-top: 5px;">
                        ${new Date(review.created_at).toLocaleDateString()}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    async saveBook() {
        const title = document.getElementById('bookTitle').value.trim();
        const author = document.getElementById('bookAuthor').value.trim();
        const isbn = document.getElementById('bookIsbn').value.trim();
        const description = document.getElementById('bookDescription').value.trim();
        const year = document.getElementById('bookYear').value;
        
        if (!title || !author) {
            this.showAlert('Please fill in title and author', 'error');
            return;
        }
        
        const bookData = {
            title,
            author,
            isbn: isbn || null,
            description: description || null,
            publication_year: year ? parseInt(year) : null
        };
        
        try {
            const response = await fetch(`${this.baseURL}/books`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(bookData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showAlert('Book added successfully!', 'success');
                this.closeModal('addBookModal');
                document.getElementById('bookForm').reset();
                this.loadBooks();
            } else {
                this.showAlert(`Error: ${result.error || 'Failed to add book'}`, 'error');
            }
        } catch (error) {
            this.showAlert('Failed to connect to server', 'error');
        }
    }

    async saveReview() {
        if (!this.selectedBookId) {
            this.showAlert('Please select a book first', 'error');
            return;
        }
        
        const name = document.getElementById('reviewerName').value.trim();
        const email = document.getElementById('reviewerEmail').value.trim();
        const rating = document.getElementById('reviewRating').value;
        const text = document.getElementById('reviewText').value.trim();
        
        if (!name || !rating) {
            this.showAlert('Please fill in your name and rating', 'error');
            return;
        }
        
        const reviewData = {
            reviewer_name: name,
            reviewer_email: email || null,
            rating: parseFloat(rating),
            review_text: text || null
        };
        
        try {
            const response = await fetch(`${this.baseURL}/books/${this.selectedBookId}/reviews`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(reviewData)
            });
            
            const result = await response.json();
            
            if (response.ok) {
                this.showAlert('Review added successfully!', 'success');
                this.closeModal('addReviewModal');
                document.getElementById('reviewForm').reset();
                this.loadReviews(this.selectedBookId);
                this.loadReviewStats(this.selectedBookId);
            } else {
                this.showAlert(`Error: ${result.error || 'Failed to add review'}`, 'error');
            }
        } catch (error) {
            this.showAlert('Failed to connect to server', 'error');
        }
    }

    showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type}`;
        alertDiv.innerHTML = `
            ${message}
            <span style="float: right; cursor: pointer;" onclick="this.parentElement.remove()">&times;</span>
        `;
        
        // Insert at top of container
        const container = document.querySelector('.container');
        container.insertBefore(alertDiv, container.firstChild);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (alertDiv.parentNode) {
                alertDiv.remove();
            }
        }, 5000);
    }

    escapeHtml(text) {
        if (!text) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Modal functions
function showAddBookModal() {
    document.getElementById('addBookModal').style.display = 'block';
}

function showAddReviewModal() {
    if (!app.selectedBookId) {
        app.showAlert('Please select a book first', 'error');
        return;
    }
    document.getElementById('addReviewModal').style.display = 'block';
}

function closeModal(modalId) {
    document.getElementById(modalId).style.display = 'none';
}

// Close modal when clicking outside
window.onclick = function(event) {
    const modals = document.querySelectorAll('.modal');
    modals.forEach(modal => {
        if (event.target === modal) {
            modal.style.display = 'none';
        }
    });
}

// Initialize app when page loads
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new BookReviewApp();
});