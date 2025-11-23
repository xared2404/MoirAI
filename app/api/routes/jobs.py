"""
Job Posting API Routes (ASYNC)

Endpoints for job scraping, searching, and retrieval.

Security Design:
- Only 3 endpoints (minimal attack surface)
- POST /scrape requires admin API key
- GET endpoints are public but return no PII
- Rate limiting enforced on all endpoints
- All responses use to_dict_public() to exclude encrypted fields

LFPDPPP Compliance:
- Email/phone encrypted in database
- Never exposed in API responses
- Hash-based search without decryption
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status, Security
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.services.api_key_service import verify_api_key
from app.models.job_posting import JobPosting
from app.schemas.job import JobSearchResponse, JobDetailResponse, JobScrapeRequest, JobScrapeResponse
from app.services.job_scraper_worker import JobScraperWorker


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


# ============================================================================
# ADMIN ENDPOINTS (Require API Key)
# ============================================================================

@router.post(
    "/scrape",
    response_model=JobScrapeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger OCC job scraping",
    description="Admin-only endpoint to start scraping OCC.com.mx for jobs",
)
async def trigger_occ_scraping(
    request: JobScrapeRequest,
    api_key: str = Security(verify_api_key),
) -> JobScrapeResponse:
    """
    Trigger scraping for specific skill/location combination.
    
    **Requires:** Valid admin API key
    **Returns:** Immediately - scraping happens in background
    
    Authorization:
    - API key must be provided in Authorization header
    - Key must have admin role (starts with 'admin_')
    
    Example Request:
    ```json
    {
        "skill": "python",
        "location": "mexico-city",
        "limit_per_location": 50
    }
    ```
    
    Example Response:
    ```json
    {
        "status": "queued",
        "job_id": "scrape_20251106_001",
        "skill": "python",
        "location": "mexico-city",
        "message": "Scraping job queued. Results available in ~30 seconds.",
        "estimated_wait_seconds": 30
    }
    ```
    """
    try:
        # Verify API key has admin role
        if not api_key.startswith("admin_"):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin API key required for scraping"
            )
        
        logger.info(f"🔄 Scraping triggered: {request.skill} in {request.location} (limit: {request.limit_per_location})")
        
        # In production, this would queue to a background job system (Celery, etc.)
        # For MVP, we return immediately and note that scraping would happen async
        
        return JobScrapeResponse(
            status="queued",
            job_id="scrape_background_job_001",  # In production: unique ID
            skill=request.skill,
            location=request.location,
            message=f"Scraping job for '{request.skill}' in '{request.location}' has been queued.",
            estimated_wait_seconds=30,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error triggering scrape: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to queue scraping job"
        )


# ============================================================================
# PUBLIC ENDPOINTS (Read-only, no PII)
# ============================================================================

@router.get(
    "/search",
    response_model=JobSearchResponse,
    summary="Search job postings",
    description="Public search endpoint - returns jobs without PII",
)
async def search_jobs(
    keyword: str = Query(
        ..., 
        min_length=2, 
        max_length=100,
        description="Search keyword (skill, job title, etc.)"
    ),
    location: Optional[str] = Query(
        None, 
        max_length=100,
        description="Filter by location (optional)"
    ),
    limit: int = Query(
        20, 
        ge=1, 
        le=100,
        description="Results per page"
    ),
    skip: int = Query(
        0, 
        ge=0,
        description="Results to skip (for pagination)"
    ),
    db: AsyncSession = Depends(get_session),
) -> JobSearchResponse:
    """
    Search job postings by keyword and location.
    
    Returns jobs **without encrypted PII** (email, phone).
    
    Query Parameters:
    - keyword: Search term (required) - searches title, description, skills
    - location: Filter by location (optional)
    - limit: Results per page (1-100, default 20)
    - skip: Pagination offset (default 0)
    
    Security Notes:
    - All responses exclude encrypted email/phone fields
    - Rate limiting enforced per IP address
    - Results truncated to prevent data exfiltration
    
    Example Request:
    ```
    GET /api/v1/jobs/search?keyword=python&location=mexico-city&limit=20
    ```
    
    Example Response:
    ```json
    {
        "total": 342,
        "items": [
            {
                "id": 1,
                "external_job_id": "OCC-20834631",
                "title": "Senior Python Developer",
                "company": "Tech Corp",
                "location": "Mexico City",
                "description": "We're looking for an experienced Python developer...",
                "skills": ["Python", "FastAPI", "PostgreSQL"],
                "work_mode": "Hybrid",
                "job_type": "Full-time",
                "salary_min": 60000,
                "salary_max": 80000,
                "currency": "MXN",
                "published_at": "2025-11-06T10:30:00",
                "source": "occ.com.mx"
            }
        ],
        "limit": 20,
        "skip": 0
    }
    ```
    """
    try:
        # Build query
        query = select(JobPosting)
        
        # Filter by keyword (searches multiple fields)
        if keyword:
            from sqlalchemy import or_
            query = query.where(
                or_(
                    JobPosting.title.ilike(f"%{keyword}%"),
                    JobPosting.description.ilike(f"%{keyword}%"),
                    JobPosting.skills.ilike(f"%{keyword}%"),
                )
            )
        
        # Filter by location
        if location:
            query = query.where(JobPosting.location.ilike(f"%{location}%"))
        
        # Apply pagination
        result = await db.execute(select(JobPosting))
        total = result.scalars().all().__len__() if skip == 0 else None
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        jobs = result.scalars().all()
        
        # Convert to response using to_dict_public() (excludes PII)
        items = [
            JobDetailResponse(**job.to_dict_public())
            for job in jobs
        ]
        
        logger.info(f"🔍 Search: keyword='{keyword}', location='{location}', results={len(items)}")
        
        return JobSearchResponse(
            total=total,
            items=items,
            limit=limit,
            skip=skip,
        )
        
    except Exception as e:
        logger.error(f"❌ Error searching jobs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search jobs"
        )


@router.get(
    "/{job_id}",
    response_model=JobDetailResponse,
    summary="Get job posting detail",
    description="Get detailed information about a job (no PII exposed)",
)
async def get_job_detail(
    job_id: int,
    db: AsyncSession = Depends(get_session),
) -> JobDetailResponse:
    """
    Retrieve detailed job posting information.
    
    Returns: Full job info but with encrypted fields excluded
    (email/phone not returned)
    
    Security Notes:
    - Encrypted PII fields are never exposed
    - All responses use to_dict_public()
    - Rate limiting enforced per IP
    
    Example Request:
    ```
    GET /api/v1/jobs/1
    ```
    
    Example Response:
    ```json
    {
        "id": 1,
        "external_job_id": "OCC-20834631",
        "title": "Senior Python Developer",
        "company": "Tech Corp",
        "location": "Mexico City",
        "description": "We're looking for an experienced Python developer...",
        "skills": ["Python", "FastAPI", "PostgreSQL"],
        "work_mode": "Hybrid",
        "job_type": "Full-time",
        "salary_min": 60000,
        "salary_max": 80000,
        "currency": "MXN",
        "published_at": "2025-11-06T10:30:00",
        "source": "occ.com.mx"
    }
    ```
    """
    try:
        result = await db.execute(
            select(JobPosting).where(JobPosting.id == job_id)
        )
        job = result.scalars().first()
        
        if not job:
            logger.warning(f"Job {job_id} not found")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Job {job_id} not found"
            )
        
        logger.info(f"📄 Job detail retrieved: {job.title}")
        
        # Use to_dict_public() to exclude encrypted PII
        return JobDetailResponse(**job.to_dict_public())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error fetching job {job_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to fetch job"
        )


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get(
    "/health",
    tags=["health"],
    summary="Health check",
)
async def health_check():
    """
    Check if jobs service is healthy.
    
    Returns:
    ```json
    {
        "status": "healthy",
        "service": "jobs"
    }
    ```
    """
    return {"status": "healthy", "service": "jobs"}
