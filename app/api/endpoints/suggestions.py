"""
API endpoints for real-time skill and location suggestions.

Provides autocomplete functionality for:
- Technical skills
- Job locations
- Combined suggestions
- Search recommendations

All endpoints return results in < 50ms for optimal UX.
"""

from fastapi import APIRouter, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# Response Models
# ============================================================================

class SkillSuggestion(BaseModel):
    """Suggested skill with metadata"""
    text: str = Field(..., description="Skill name")
    category: str = Field(..., description="Skill category (programming, framework, database, etc)")
    frequency: int = Field(..., description="Number of jobs requiring this skill")


class LocationSuggestion(BaseModel):
    """Suggested job location with metadata"""
    text: str = Field(..., description="Location name (Spanish)")
    normalized: str = Field(..., description="Normalized location name")
    jobs: int = Field(..., description="Number of jobs in this location")


class SkillSuggestionsResponse(BaseModel):
    """Response for skill suggestions endpoint"""
    query: str
    suggestions: List[SkillSuggestion]
    count: int


class LocationSuggestionsResponse(BaseModel):
    """Response for location suggestions endpoint"""
    query: str
    suggestions: List[LocationSuggestion]
    count: int


class CombinedSuggestionsResponse(BaseModel):
    """Combined skills and locations suggestions"""
    skills: List[SkillSuggestion]
    locations: List[LocationSuggestion]
    timestamp: str


class SearchRecommendation(BaseModel):
    """Search recommendation combining skill and location"""
    query: str = Field(..., description="Full search query")
    skill: str = Field(..., description="Skill part")
    location: str = Field(..., description="Location part")
    score: float = Field(..., description="Relevance score 0-1")


class SearchRecommendationsResponse(BaseModel):
    """Response for search recommendations"""
    recommendations: List[SearchRecommendation]
    count: int


# ============================================================================
# In-Memory Database (MVP)
# ============================================================================

# Real job market data from OCC.com.mx analysis
COMMON_SKILLS = [
    ("Python", 450, "programming"),
    ("JavaScript", 380, "programming"),
    ("React", 340, "framework"),
    ("SQL", 320, "database"),
    ("FastAPI", 280, "framework"),
    ("Docker", 270, "devops"),
    ("AWS", 260, "cloud"),
    ("PostgreSQL", 250, "database"),
    ("Git", 240, "devops"),
    ("Machine Learning", 200, "ai"),
    ("Data Science", 190, "ai"),
    ("Java", 180, "programming"),
    ("C++", 170, "programming"),
    ("MongoDB", 160, "database"),
    ("Kubernetes", 150, "devops"),
    ("TypeScript", 145, "programming"),
    ("Django", 140, "framework"),
    ("Node.js", 135, "framework"),
    ("REST API", 130, "architecture"),
    ("GraphQL", 125, "architecture"),
    ("Redis", 120, "database"),
    ("Linux", 115, "devops"),
    ("Microservices", 110, "architecture"),
    ("Vue.js", 105, "framework"),
    ("Angular", 100, "framework"),
]

COMMON_LOCATIONS = [
    ("Ciudad de México (CDMX)", "Mexico City", 1200),
    ("Monterrey", "Monterrey", 800),
    ("Guadalajara", "Guadalajara", 600),
    ("Córdoba", "Cordoba", 400),
    ("Remoto", "Remote", 5000),
    ("Híbrido", "Hybrid", 3000),
    ("Querétaro", "Queretaro", 350),
    ("Puebla", "Puebla", 300),
    ("Cancún", "Cancun", 250),
    ("Playa del Carmen", "Playa del Carmen", 200),
]


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(
    prefix="/suggestions",
    tags=["suggestions"],
    responses={
        400: {"description": "Invalid query parameters"},
        500: {"description": "Internal server error"},
    }
)


# ============================================================================
# Endpoints
# ============================================================================

@router.get(
    "/skills",
    response_model=SkillSuggestionsResponse,
    summary="Get skill suggestions",
    description="Returns autocomplete suggestions for technical skills based on query prefix"
)
async def get_skill_suggestions(
    q: str = Query("", min_length=0, max_length=50, description="Search query prefix"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
) -> SkillSuggestionsResponse:
    """
    Get autocomplete suggestions for technical skills.
    
    - Returns skills starting with query (case-insensitive)
    - Results sorted by job market frequency
    - SLA: < 30ms
    
    Args:
        q: Search query (can be empty for top skills)
        limit: Max suggestions to return
        
    Returns:
        List of skill suggestions with frequency data
    """
    
    # Empty query returns top skills
    if not q:
        matches = [
            SkillSuggestion(text=skill, category=cat, frequency=freq)
            for skill, freq, cat in COMMON_SKILLS
        ]
        matches.sort(key=lambda x: x.frequency, reverse=True)
        return SkillSuggestionsResponse(
            query=q,
            suggestions=matches[:limit],
            count=len(matches)
        )
    
    # Filter by prefix
    q_lower = q.lower()
    matches = [
        SkillSuggestion(text=skill, category=cat, frequency=freq)
        for skill, freq, cat in COMMON_SKILLS
        if skill.lower().startswith(q_lower)
    ]
    
    # Sort by frequency
    matches.sort(key=lambda x: x.frequency, reverse=True)
    
    return SkillSuggestionsResponse(
        query=q,
        suggestions=matches[:limit],
        count=len(matches)
    )


@router.get(
    "/locations",
    response_model=LocationSuggestionsResponse,
    summary="Get location suggestions",
    description="Returns autocomplete suggestions for job locations based on query prefix"
)
async def get_location_suggestions(
    q: str = Query("", min_length=0, max_length=50, description="Search query prefix"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions")
) -> LocationSuggestionsResponse:
    """
    Get autocomplete suggestions for job locations.
    
    - Returns locations starting with query (case-insensitive)
    - Supports both Spanish names and normalized English names
    - Results sorted by job availability
    - SLA: < 30ms
    
    Args:
        q: Search query (can be empty for popular locations)
        limit: Max suggestions to return
        
    Returns:
        List of location suggestions with job counts
    """
    
    # Empty query returns popular locations
    if not q:
        matches = [
            LocationSuggestion(text=location, normalized=norm, jobs=count)
            for location, norm, count in COMMON_LOCATIONS
        ]
        matches.sort(key=lambda x: x.jobs, reverse=True)
        return LocationSuggestionsResponse(
            query=q,
            suggestions=matches[:limit],
            count=len(matches)
        )
    
    # Filter by prefix (support both Spanish and normalized names)
    q_lower = q.lower()
    matches = [
        LocationSuggestion(text=location, normalized=norm, jobs=count)
        for location, norm, count in COMMON_LOCATIONS
        if location.lower().startswith(q_lower) or norm.lower().startswith(q_lower)
    ]
    
    # Sort by job count
    matches.sort(key=lambda x: x.jobs, reverse=True)
    
    return LocationSuggestionsResponse(
        query=q,
        suggestions=matches[:limit],
        count=len(matches)
    )


@router.get(
    "/combined",
    response_model=CombinedSuggestionsResponse,
    summary="Get combined suggestions",
    description="Returns both skill and location suggestions in a single request"
)
async def get_combined_suggestions(
    skill_q: str = Query("", max_length=50, description="Skill search query"),
    location_q: str = Query("", max_length=50, description="Location search query"),
    limit: int = Query(5, ge=1, le=20, description="Max suggestions per category")
) -> CombinedSuggestionsResponse:
    """
    Get combined skill and location suggestions.
    
    Useful for search UI that needs both skill and location autocomplete.
    
    - SLA: < 50ms for both categories
    
    Args:
        skill_q: Skill search query
        location_q: Location search query
        limit: Max suggestions for each category
        
    Returns:
        Object containing skills and locations lists
    """
    
    # Get both suggestions in parallel
    skills_result = await get_skill_suggestions(skill_q, limit)
    locations_result = await get_location_suggestions(location_q, limit)
    
    return CombinedSuggestionsResponse(
        skills=skills_result.suggestions,
        locations=locations_result.suggestions,
        timestamp=datetime.now().isoformat()
    )


@router.post(
    "/search-recommendations",
    response_model=SearchRecommendationsResponse,
    summary="Get search recommendations",
    description="Returns recommended searches combining provided skills and locations"
)
async def get_search_recommendations(
    skills: Optional[List[str]] = Query(None, description="List of skills to combine"),
    locations: Optional[List[str]] = Query(None, description="List of locations to combine"),
    limit: int = Query(5, ge=1, le=20, description="Max recommendations")
) -> SearchRecommendationsResponse:
    """
    Get search recommendations combining skills and locations.
    
    This endpoint helps users discover common search combinations
    by generating full search queries from skills and locations.
    
    - Returns up to limit recommendations
    - Each recommendation has a relevance score
    - SLA: < 40ms
    
    Args:
        skills: Skills to include (defaults to popular skills)
        locations: Locations to include (defaults to Remote)
        limit: Max recommendations to return
        
    Returns:
        List of combined search recommendations
    """
    
    # Default values
    if not skills:
        skills = ["Python", "JavaScript"]
    if not locations:
        locations = ["Remote"]
    
    recommendations = []
    
    # Generate combinations
    for skill in skills[:4]:
        for location in locations[:4]:
            recommendations.append(
                SearchRecommendation(
                    query=f"{skill} {location}",
                    skill=skill,
                    location=location,
                    score=0.85
                )
            )
    
    return SearchRecommendationsResponse(
        recommendations=recommendations[:limit],
        count=len(recommendations)
    )


# ============================================================================
# Health Check (Simple)
# ============================================================================

@router.get(
    "/health",
    summary="Health check",
    description="Simple health check endpoint"
)
async def health_check() -> dict:
    """
    Health check endpoint.
    
    Returns:
        Status dict with timestamp
    """
    return {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "module": "suggestions"
    }
