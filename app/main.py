"""
FastAPI application initialization.
Educational Query Classifier API for WhatsApp integration.
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.core.logging_config import logger
from app.api.routes import router
from app.utils.exceptions import ClassifierException


# Initialize FastAPI application
app = FastAPI(
    title=settings.api_title,
    version=settings.api_version,
    description=settings.api_description,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler for ClassifierException
@app.exception_handler(ClassifierException)
async def classifier_exception_handler(request: Request, exc: ClassifierException):
    """Handle classifier-specific exceptions."""
    logger.error(f"ClassifierException: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "ClassificationError",
            "message": str(exc),
            "detail": "An error occurred during classification"
        }
    )


# Global exception handler for unexpected errors
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "detail": str(exc) if settings.environment == "development" else None
        }
    )


# Startup event
@app.on_event("startup")
async def startup_event():
    """Run on application startup."""
    logger.info(f"Starting {settings.api_title} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    logger.info(f"OpenAI Model: {settings.openai_model}")


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Run on application shutdown."""
    logger.info(f"Shutting down {settings.api_title}")


# Include routers
app.include_router(router, tags=["Classification"])


# Health check for load balancers/monitoring
@app.get("/ping")
async def ping():
    """Simple ping endpoint for monitoring."""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.environment == "development"
    )
