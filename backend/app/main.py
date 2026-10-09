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

# Allow CORS for Next.js frontend
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8000",
    "http://127.0.0.1:8000",
]

# Include the deployed frontend origin when configured
if settings.FRONTEND_URL:
    _frontend_url = settings.FRONTEND_URL.strip().rstrip("/")
    if _frontend_url and _frontend_url not in origins:
        origins.append(_frontend_url)

# Honor the CORS_ORIGINS setting
for _origin in settings.CORS_ORIGINS:
    _origin = _origin.strip().rstrip("/")
    if _origin and _origin not in origins:
        origins.append(_origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
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
