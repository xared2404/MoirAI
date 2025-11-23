"""
Job API Response Schemas

Pydantic models for job-related API responses.
All schemas exclude encrypted PII fields (email, phone).

Security Notes:
- JobDetailResponse and JobSearchResponse use to_dict_public() to ensure
  encrypted fields are never exposed in API responses
- Sensitive data (email_hash, phone_hash) is also excluded
- Only public information is returned
"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


class JobDetailResponse(BaseModel):
    """
    Job posting detail response (no PII exposed).
    
    Safe to return in public API responses.
    Excludes encrypted email/phone fields.
    """
    id: int = Field(..., description="Database ID")
    external_job_id: str = Field(..., description="ID from source (OCC, etc.)")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Job description (may be truncated)")
    skills: Optional[List[str]] = Field(default=None, description="Required skills")
    work_mode: Optional[str] = Field(None, description="Remote/Onsite/Hybrid")
    job_type: Optional[str] = Field(None, description="Full-time/Part-time/Contract")
    salary_min: Optional[float] = Field(None, description="Minimum salary in MXN")
    salary_max: Optional[float] = Field(None, description="Maximum salary in MXN")
    currency: str = Field("MXN", description="Currency code")
    published_at: Optional[datetime] = Field(None, description="Publication date")
    source: str = Field("occ.com.mx", description="Data source")
    
    class Config:
        from_attributes = True
        example = {
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
            "source": "occ.com.mx",
        }


class JobSearchResponse(BaseModel):
    """
    Job search results response.
    
    Paginated response for job search queries.
    """
    total: Optional[int] = Field(
        None, 
        description="Total jobs matching query (only on first page)"
    )
    items: List[JobDetailResponse] = Field(
        ..., 
        description="Jobs in this page"
    )
    limit: int = Field(
        ..., 
        description="Max results per page", 
        ge=1, 
        le=100
    )
    skip: int = Field(
        ..., 
        description="Number of results skipped", 
        ge=0
    )
    
    class Config:
        from_attributes = True
        example = {
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
                    "source": "occ.com.mx",
                }
            ],
            "limit": 20,
            "skip": 0,
        }


class JobScrapeRequest(BaseModel):
    """Request model for triggering scraping."""
    skill: str = Field(..., min_length=2, max_length=50, description="Skill to search for")
    location: str = Field("remote", min_length=2, max_length=100, description="Location to search in")
    limit_per_location: int = Field(20, ge=1, le=100, description="Max jobs per location")


class JobScrapeResponse(BaseModel):
    """Response for scraping request."""
    status: str = Field(..., description="Job status (queued, processing, completed, failed)")
    job_id: Optional[str] = Field(None, description="Background job ID for tracking")
    skill: str = Field(..., description="Skill being scraped")
    location: str = Field(..., description="Location being scraped")
    message: str = Field(..., description="Status message")
    estimated_wait_seconds: Optional[int] = Field(
        None, 
        description="Estimated wait time before results available"
    )
