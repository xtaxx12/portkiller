"""
PortKiller - Main Application Entry Point

A modern port management tool for developers and DevOps engineers.
"""
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes.ports import router as ports_router

# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API routes
app.include_router(ports_router)

# Static files directory
STATIC_DIR = Path(__file__).parent / "app" / "static"

# Mount static files if directory exists
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


@app.get("/", include_in_schema=False)
async def root():
    """Serve the main application page."""
    index_path = STATIC_DIR / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {
        "message": "Welcome to PortKiller API",
        "docs": "/docs",
        "version": settings.APP_VERSION
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


def main():
    """Run the application."""
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🔌 PortKiller v{settings.APP_VERSION}                                        ║
║   Port Management & Process Control Tool                     ║
║                                                              ║
║   ➜  Local:   http://{settings.HOST}:{settings.PORT}                        ║
║   ➜  API:     http://{settings.HOST}:{settings.PORT}/docs                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG
    )


if __name__ == "__main__":
    main()
