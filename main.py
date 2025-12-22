"""
PortKiller - Main Application Entry Point

A modern port management tool for developers and DevOps engineers.
Desktop application with native window using pywebview.
"""

import io
import os
import sys
import threading
from pathlib import Path


def fix_frozen_stdio():
    """Fix stdout/stderr for PyInstaller frozen mode (windowed)."""
    if getattr(sys, 'frozen', False):
        if sys.stdout is None:
            sys.stdout = open(os.devnull, 'w', encoding='utf-8')
        if sys.stderr is None:
            sys.stderr = open(os.devnull, 'w', encoding='utf-8')


# Apply fix before importing other modules
fix_frozen_stdio()

import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routes.ports import router as ports_router


def get_base_path() -> Path:
    """Get the base path for resources (handles PyInstaller frozen mode)."""
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description=settings.APP_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Include API routes
app.include_router(ports_router)

# Static files directory
BASE_PATH = get_base_path()
STATIC_DIR = BASE_PATH / "app" / "static"

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
        "version": settings.APP_VERSION,
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": settings.APP_VERSION}


def run_server():
    """Run the uvicorn server in a separate thread."""
    config = uvicorn.Config(
        app,
        host=settings.HOST,
        port=settings.PORT,
        log_config=None,
        access_log=False,
    )
    server = uvicorn.Server(config)
    server.run()


def main():
    """Run the application."""
    is_frozen = getattr(sys, 'frozen', False)
    
    if is_frozen:
        # Desktop mode: Run server in background thread and show native window
        import webview
        
        # Start the API server in a background thread
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for the server to start
        import time
        time.sleep(1)
        
        # Create native desktop window
        window = webview.create_window(
            title=f"PortKiller v{settings.APP_VERSION}",
            url=f"http://{settings.HOST}:{settings.PORT}",
            width=1200,
            height=800,
            resizable=True,
            min_size=(800, 600),
        )
        
        # Start the webview (blocks until window is closed)
        webview.start()
    else:
        # Development mode: Standard uvicorn with reload
        print(
            f"""
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║   🔌 PortKiller v{settings.APP_VERSION}                                        ║
║   Port Management & Process Control Tool                     ║
║                                                              ║
║   ➜  Local:   http://{settings.HOST}:{settings.PORT}                        ║
║   ➜  API:     http://{settings.HOST}:{settings.PORT}/docs                   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """
        )
        uvicorn.run("main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)


if __name__ == "__main__":
    main()
