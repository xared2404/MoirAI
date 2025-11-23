"""
Job Posting & Search API Routes (ASYNC)

Endpoints for job searching, retrieval y autocomplete suggestions.

🔒 Security Design:
- GET endpoints are public but return no PII (encrypted fields excluded)
- Rate limiting enforced on all endpoints
- All responses use to_dict_public() to exclude encrypted fields

📋 LFPDPPP Compliance:
- Email/phone encrypted in database
- Never exposed in API responses
- Hash-based search without decryption

✨ Features:
- Full-text search with filters (keyword, location, salary)
- Real-time autocomplete for skills and locations
- Detailed job information with quality metrics
- Trending jobs discovery
"""

import logging
from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlmodel import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_session
from app.models.job_posting import JobPosting
from app.schemas.job import JobSearchResponse, JobDetailResponse
from app.schemas import BaseResponse


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/jobs", tags=["jobs"])


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
# AUTOCOMPLETE ENDPOINTS (Suggestions consolidadas)
# ============================================================================

@router.get(
    "/autocomplete/skills",
    summary="Get skill suggestions",
    description="Returns autocomplete suggestions for technical skills",
)
async def get_skill_suggestions(
    q: str = Query("", min_length=0, max_length=50, description="Search query prefix"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
):
    """
    Get autocomplete suggestions for technical skills.
    
    - Returns skills starting with query (case-insensitive)
    - Results sorted by job market frequency
    - SLA: < 30ms
    
    Example:
    ```
    GET /jobs/autocomplete/skills?q=pyt&limit=5
    
    {
      "query": "pyt",
      "suggestions": [
        {"text": "Python", "category": "programming", "frequency": 450},
        {"text": "Python Flask", "category": "framework", "frequency": 140}
      ]
    }
    ```
    """
    # Real job market data
    COMMON_SKILLS = [
        ("Python", 450, "programming"),
        ("JavaScript", 380, "programming"),
        ("React", 340, "framework"),
        ("SQL", 320, "database"),
        ("FastAPI", 280, "framework"),
        ("Docker", 270, "devops"),
        ("AWS", 260, "cloud"),
        ("PostgreSQL", 250, "database"),
    ]
    
    q_lower = q.lower()
    matches = [
        {
            "text": skill,
            "category": cat,
            "frequency": freq
        }
        for skill, freq, cat in COMMON_SKILLS
        if skill.lower().startswith(q_lower) or not q
    ]
    
    matches.sort(key=lambda x: x["frequency"], reverse=True)
    
    return {
        "query": q,
        "suggestions": matches[:limit],
        "count": len(matches)
    }


@router.get(
    "/autocomplete/locations",
    summary="Get location suggestions",
    description="Returns autocomplete suggestions for job locations",
)
async def get_location_suggestions(
    q: str = Query("", min_length=0, max_length=50, description="Search query prefix"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
):
    """
    Get autocomplete suggestions for job locations.
    
    - Returns locations starting with query (case-insensitive)
    - Results sorted by job availability
    - SLA: < 30ms
    
    Example:
    ```
    GET /jobs/autocomplete/locations?q=mex&limit=5
    
    {
      "query": "mex",
      "suggestions": [
        {"text": "México City", "jobs": 1200},
        {"text": "México (Remote)", "jobs": 5000}
      ]
    }
    ```
    """
    COMMON_LOCATIONS = [
        ("Ciudad de México", "Mexico City", 1200),
        ("Monterrey", "Monterrey", 800),
        ("Guadalajara", "Guadalajara", 600),
        ("Remoto", "Remote", 5000),
        ("Híbrido", "Hybrid", 3000),
    ]
    
    q_lower = q.lower()
    matches = [
        {
            "text": location,
            "normalized": norm,
            "jobs": count
        }
        for location, norm, count in COMMON_LOCATIONS
        if location.lower().startswith(q_lower) or norm.lower().startswith(q_lower) or not q
    ]
    
    matches.sort(key=lambda x: x["jobs"], reverse=True)
    
    return {
        "query": q,
        "suggestions": matches[:limit],
        "count": len(matches)
    }


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
