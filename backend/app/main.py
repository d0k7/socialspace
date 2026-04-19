"""
SocialSpace FastAPI Application
================================

Web server that exposes the socialspace_agent platform library
via REST API endpoints.

Author: Dheeraj Mishra
Created: April 2, 2026
Phase: Foundation - FastAPI Web Server
"""

from fastapi import FastAPI
from app.routers import auth as auth_router
from app.routers import twitter as twitter_router
from app.routers import telegram as telegram_router
from fastapi.middleware.cors import CORSMiddleware
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="SocialSpace API",
    description="AI-powered social media management platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.include_router(auth_router.router)
app.include_router(twitter_router.router)
app.include_router(telegram_router.router)

# CORS Configuration
# WHY: Frontend (React) runs on different port (3000/5173)
#      Browser blocks requests without CORS headers
# JUSTIFICATION: Allow frontend to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React dev server (default)
        "http://localhost:5173",      # Vite dev server (default)
        "http://localhost:5174",      # Vite alternate port
        "http://127.0.0.1:3000",      # Alternate localhost
        "http://127.0.0.1:5173",      # Alternate localhost
    ],
    allow_credentials=True,
    allow_methods=["*"],              # Allow all HTTP methods
    allow_headers=["*"],              # Allow all headers
)


# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    WHY: Verify server is running
    USE: Monitoring, CI/CD, load balancers
    
    Returns:
        dict: Status information
        
    Example:
        GET /health
        Response: {"status": "healthy", "version": "1.0.0"}
    """
    return {
        "status": "healthy",
        "version": "1.0.0",
        "platform_library": "socialspace_agent",
        "api_docs": "/docs",
        "message": "SocialSpace API is running!"
    }


# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/")
async def root():
    """
    Root endpoint.
    
    WHY: Provide API information and links
    USE: Quick reference for developers
    
    Returns:
        dict: Welcome message and navigation links
    """
    return {
        "message": "Welcome to SocialSpace API 🚀",
        "version": "1.0.0",
        "status": "operational",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        },
        "endpoints": {
            "health_check": "/health",
            "auth": "/api/auth (coming soon)",
            "posts": "/api/posts (coming soon)",
            "platforms": "/api/platforms (coming soon)"
        },
        "platform_library": {
            "name": "socialspace_agent",
            "platforms": [
                "WhatsApp", "Telegram", "Instagram", "Discord",
                "Reddit", "Twitter", "YouTube", "Facebook",
                "LinkedIn", "TikTok", "Snapchat", "Pinterest"
            ]
        }
    }


# ============================================
# TEST ENDPOINT - VERIFY PLATFORM LIBRARY
# ============================================

@app.get("/test/platform-library")
async def test_platform_library():
    """
    Test endpoint to verify platform library import.
    
    WHY: Ensure socialspace_agent is accessible
    USE: Debugging, verification
    
    Returns:
        dict: Platform library information
    """
    try:
        # Try importing the platform library
        from socialspace_agent.platforms.factory import PlatformFactory
        
        # Try to get version (may not exist)
        try:
            from socialspace_agent import __version__ as agent_version
        except ImportError:
            agent_version = "1.0.0"  # Default if __version__ not defined
        
        # Get available platforms
        available_platforms = PlatformFactory.get_available_platforms()
        
        return {
            "status": "success",
            "library_imported": True,
            "library_version": agent_version,
            "available_platforms": available_platforms,
            "platform_count": len(available_platforms),
            "message": "✅ Platform library is accessible and working!"
        }
    except ImportError as e:
        return {
            "status": "error",
            "library_imported": False,
            "error": str(e),
            "message": "❌ Failed to import platform library"
        }
    except Exception as e:
        return {
            "status": "error",
            "library_imported": False,
            "error": str(e),
            "message": "❌ Unexpected error accessing platform library"
        }


# ============================================
# STARTUP EVENT
# ============================================

@app.on_event("startup")
async def startup_event():
    """
    Run on application startup.
    
    WHY: Initialize resources, connections, etc.
    """
    logger.info("=" * 60)
    logger.info("🚀 SocialSpace API Starting Up...")
    logger.info("=" * 60)
    logger.info("✅ FastAPI application initialized")
    logger.info("✅ CORS middleware configured")
    logger.info("✅ Platform library: socialspace_agent")
    logger.info("=" * 60)
    logger.info("📚 API Documentation:")
    logger.info("   - Swagger UI: http://localhost:8000/docs")
    logger.info("   - ReDoc:      http://localhost:8000/redoc")
    logger.info("=" * 60)
    logger.info("🔗 Endpoints:")
    logger.info("   - Root:       http://localhost:8000/")
    logger.info("   - Health:     http://localhost:8000/health")
    logger.info("   - Test:       http://localhost:8000/test/platform-library")
    logger.info("=" * 60)


# ============================================
# SHUTDOWN EVENT
# ============================================

@app.on_event("shutdown")
async def shutdown_event():
    """
    Run on application shutdown.
    
    WHY: Cleanup resources, close connections
    """
    logger.info("=" * 60)
    logger.info("👋 SocialSpace API Shutting Down...")
    logger.info("=" * 60)


# ============================================
# MAIN ENTRY POINT
# ============================================

if __name__ == "__main__":
    import uvicorn
    
    # Run server
    # WHY: Development server with auto-reload
    # PRODUCTION: Use gunicorn or similar
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",      # Listen on all interfaces
        port=8000,           # Default port
        reload=True,         # Auto-reload on code changes (dev only)
        log_level="info"     # Logging level
    )
