"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.logging import setup_logging, logger
from app.core.config import settings
from app.api.routes_backtest import router as backtest_router
from app.api.routes_ai import router as ai_router
from app.api.routes_logs import router as logs_router
from app.api.routes_ifvg import router as ifvg_router
from app.api.routes_daily_scorecard import router as daily_scorecard_router

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Project Forge API",
    description="Self-testing mechanical trading lab",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(backtest_router, prefix="/api")
app.include_router(ai_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(ifvg_router, prefix="/api")
app.include_router(daily_scorecard_router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Project Forge API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.on_event("startup")
async def startup():
    """Startup event."""
    logger.info("Project Forge API starting up...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Database: {settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}")


@app.on_event("shutdown")
async def shutdown():
    """Shutdown event."""
    logger.info("Project Forge API shutting down...")


