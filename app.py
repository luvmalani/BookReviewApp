import os
import logging
from fastapi import Depends, FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from database import engine, Base
from routes import books, reviews
from config import settings
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from database import get_db
from sqlalchemy import text


# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Book Review API",
    description="A comprehensive book review service with caching and database integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Create database tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(books.router, prefix="/api", tags=["books"])
app.include_router(reviews.router, prefix="/api", tags=["reviews"])

@app.on_event("startup")
async def startup_db_check():
    try:
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))  # Simple query to verify connection
        logger.info(" Database connection successful")
    except OperationalError as e:
        logger.error(f" Database connection failed: {e}")
    except Exception as e:
        logger.error(f" Unexpected error during DB startup check: {e}")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    """Serve the main HTML interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "service": "book-review-api"}

@app.get("/check-db")
def check_db_connection(db: Session = Depends(get_db)):
    try:
        db.execute("SELECT 1")
        return {"status": "connected"}
    except Exception as e:
        return {"status": "not connected", "detail": str(e)}


@app.get("/db-health")
async def db_health():
    try:
        db: Session = next(get_db())
        db.execute("SELECT 1")
        return {"status": "ok", "detail": "Database connected"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {exc}")
    return {"error": "Internal server error", "detail": str(exc)}
