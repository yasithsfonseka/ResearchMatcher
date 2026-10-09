import logging
import os
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.api.v1 import health, auth, search, papers, subjects, collections, feedback, jobs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger("app")

app = FastAPI(
    title=settings.APP_NAME,
    description="ResearchMatch: Scholarly paper discovery, categorization, and matching platform.",
    version="1.0.0",
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# If settings.CORS_ALLOWED_ORIGINS is a string, split by commas
origins = (
    [origin.strip() for origin in settings.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]
    if isinstance(settings.CORS_ALLOWED_ORIGINS, str)
    else settings.CORS_ALLOWED_ORIGINS
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception Handler to prevent leaking internal tracebacks while adding CORS headers
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global unhandled exception on {request.url}: {exc}", exc_info=True)
    origin = request.headers.get("origin", "*")
    response = JSONResponse(
        status_code=500,
        content={"detail": "An internal server error occurred. Please try again later."}
    )
    response.headers["Access-Control-Allow-Origin"] = origin
    response.headers["Access-Control-Allow-Credentials"] = "true"
    return response

# Include v1 API Routers
app.include_router(health.router, prefix=settings.API_V1_STR, tags=["Health"])
app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
app.include_router(search.router, prefix=f"{settings.API_V1_STR}/search", tags=["Search"])
app.include_router(papers.router, prefix=f"{settings.API_V1_STR}/papers", tags=["Papers"])
app.include_router(subjects.router, prefix=f"{settings.API_V1_STR}/subjects", tags=["Subjects"])
app.include_router(collections.router, prefix=f"{settings.API_V1_STR}/collections", tags=["Collections"])
app.include_router(feedback.router, prefix=f"{settings.API_V1_STR}/feedback", tags=["Feedback"])
app.include_router(jobs.router, prefix=f"{settings.API_V1_STR}/jobs", tags=["Jobs"])

@app.get("/")
def root():
    return {
        "name": settings.APP_NAME,
        "status": "online",
        "docs": "/docs",
        "disclaimer": "Discover papers from connected scholarly sources. Topic similarity does not establish that a paper supports a claim."
    }
