"""
Job Scraper Worker for background job scraping and enrichment.

Responsibilities:
- Search jobs on OCC.com.mx
- Deduplicate job postings
- Enrich job data with additional information
- Store jobs in the database

This is a minimal MVP implementation focusing on core functionality.
"""

import asyncio
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
import httpx
from app.core.session_manager import get_session_manager


# ============================================================================
# Data Models
# ============================================================================

class JobPostingMinimal(BaseModel):
    """Minimal job posting model for MVP"""
    external_job_id: str = Field(..., description="Unique job ID from source")
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    description: str = Field(..., description="Job description")
    skills: List[str] = Field(default_factory=list, description="Required skills")
    work_mode: Optional[str] = Field(None, description="Remote/Onsite/Hybrid")
    job_type: Optional[str] = Field(None, description="Full-time/Part-time/Contract")
    published_at: datetime = Field(..., description="Publication date")
    
    class Config:
        from_attributes = True


class JobSearchQuery(BaseModel):
    """Job search query parameters"""
    keyword: str = Field(..., description="Search keyword/skill", min_length=1)
    location: Optional[str] = Field(None, description="Search location")
    limit: int = Field(default=20, ge=1, le=100, description="Max results")
    skip: int = Field(default=0, ge=0, description="Results to skip")


class JobScraperResult(BaseModel):
    """Result of scraping operation"""
    query: str
    total_found: int
    jobs: List[JobPostingMinimal]
    duplicates_removed: int
    execution_time_ms: float


# ============================================================================
# Worker Class
# ============================================================================

class JobScraperWorker:
    """
    Minimal job scraper worker for MVP.
    
    Features:
    - Uses SessionManager for rate-limited HTTP requests
    - Deduplicates jobs by external_job_id
    - Tracks scraping metrics
    
    Example:
        worker = JobScraperWorker()
        jobs = await worker.search_jobs("Python", "Remote", limit=20)
    """
    
    def __init__(self, session_manager=None):
        """
        Initialize scraper worker.
        
        Args:
            session_manager: Optional custom SessionManager (for testing)
        """
        self.session_manager = session_manager or get_session_manager()
        self._seen_job_ids = set()  # Track seen jobs for deduplication
        self._occ_scraper = None  # Lazy load OCCScraper when needed
    
    async def search_jobs(
        self,
        keyword: str,
        location: Optional[str] = None,
        limit: int = 20
    ) -> List[JobPostingMinimal]:
        """
        Search for jobs on OCC.com.mx.
        
        Args:
            keyword: Search keyword (e.g., "Python")
            location: Optional location filter
            limit: Max number of jobs to return
            
        Returns:
            List of JobPostingMinimal objects
            
        Note:
            - Enforces rate limiting via SessionManager
            - Returns empty list on errors (graceful degradation)
        """
        jobs = []
        
        try:
            # 1. Enforce rate limiting
            await self.session_manager.adaptive_delay()
            
            # 2. Build search URL
            url = self._build_search_url(keyword, location)
            
            # 3. Make HTTP request
            session = await self.session_manager.get_session()
            response = await session.get(url, timeout=30.0)
            response.raise_for_status()
            
            # 4. Parse results (basic for MVP)
            jobs = self._parse_jobs_basic(response.text, keyword)
            
            return jobs[:limit]
            
        except asyncio.TimeoutError:
            print(f"⚠️  Timeout searching for '{keyword}'")
            return []
        except Exception as e:
            print(f"❌ Error searching for '{keyword}': {str(e)}")
            return []
    
    async def deduplicate_jobs(
        self,
        jobs: List[JobPostingMinimal]
    ) -> tuple[List[JobPostingMinimal], int]:
        """
        Remove duplicate jobs by external_job_id.
        
        Args:
            jobs: List of jobs to deduplicate
            
        Returns:
            Tuple of (unique_jobs, num_duplicates_removed)
        """
        unique = []
        initial_count = len(jobs)
        
        for job in jobs:
            if job.external_job_id not in self._seen_job_ids:
                self._seen_job_ids.add(job.external_job_id)
                unique.append(job)
        
        duplicates_removed = initial_count - len(unique)
        return unique, duplicates_removed
    
    async def enrich_job(self, job: JobPostingMinimal) -> JobPostingMinimal:
        """
        Enrich job data with additional information.
        
        This is a placeholder for MVP. In production, this would:
        - Extract skills using NLP
        - Categorize job type
        - Calculate salary range
        - etc.
        
        Args:
            job: Job to enrich
            
        Returns:
            Enriched job object
        """
        # MVP: Just return as-is
        # TODO: Implement NLP extraction
        return job
    
    def _build_search_url(self, keyword: str, location: Optional[str]) -> str:
        """
        Build OCC.com.mx search URL.
        
        Args:
            keyword: Search keyword
            location: Optional location filter
            
        Returns:
            Full URL for search
        """
        # Normalize keyword for URL
        keyword_slug = keyword.lower().replace(" ", "-")
        url = f"https://www.occ.com.mx/empleos/de-{keyword_slug}/"
        
        if location:
            # Add location parameter
            location_slug = location.lower().replace(" ", "-")
            url += f"?l={location_slug}"
        
        return url
    
    def _parse_jobs_basic(self, html: str, keyword: str) -> List[JobPostingMinimal]:
        """
        Parse jobs from HTML (basic MVP version).
        
        For MVP, this returns an empty list as a placeholder.
        In production, this would use BeautifulSoup to extract job data.
        
        Args:
            html: HTML content from search results
            keyword: Search keyword used
            
        Returns:
            List of parsed jobs
            
        Note:
            This is intentionally minimal for MVP. Phase 2 will implement
            full HTML parsing with BeautifulSoup.
        """
        # MVP: Return empty list (no parsing implementation yet)
        # Phase 2: Implement HTML parsing with BeautifulSoup
        # This allows the scraper infrastructure to be tested before
        # implementing complex HTML parsing
        return []
    
    def reset_duplicates_cache(self) -> None:
        """Reset the duplicates cache (useful for testing)"""
        self._seen_job_ids.clear()
    
    # ============================================================================
    # OCC-SPECIFIC SCRAPING METHODS
    # ============================================================================
    
    async def scrape_occ_jobs_by_skill(
        self,
        skill: str,
        location: str = "remote",
        page: int = 1,
        limit: int = 20,
    ) -> List[JobPostingMinimal]:
        """
        Scrapes OCC jobs for specific skill/location combination.
        
        Args:
            skill: "python", "javascript", etc.
            location: "ciudad-de-mexico", "remote", etc. (default: remote)
            page: Page number (1-indexed)
            limit: Jobs per page (20-100)
        
        Returns:
            List of JobPostingMinimal objects
            
        Example:
            jobs = await worker.scrape_occ_jobs_by_skill("python", "remote", limit=20)
        """
        try:
            # Lazy load OCCScraper if needed
            if self._occ_scraper is None:
                from app.services.occ_scraper_service import OCCScraper
                self._occ_scraper = OCCScraper()
            
            # Use OCCScraper to fetch offers
            async with self._occ_scraper as scraper:
                from app.services.occ_scraper_service import SearchFilters
                
                filters = SearchFilters(
                    keyword=skill,
                    location=location,
                    page=page,
                    sort_by="relevance"
                )
                
                offers, total = await scraper.search_jobs(filters)
            
            # Transform to JobPostingMinimal
            results = []
            for offer in offers[:limit]:
                try:
                    minimal = JobPostingMinimal(
                        external_job_id=offer.job_id,
                        title=offer.title,
                        company=offer.company,
                        location=offer.location,
                        description=offer.description or offer.full_description or "No description",
                        skills=offer.skills or [],
                        work_mode=offer.work_mode,
                        job_type=offer.job_type,
                        published_at=offer.publication_date or datetime.now(),
                    )
                    results.append(minimal)
                except Exception as e:
                    print(f"⚠️  Error transforming OCC job {offer.job_id}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            print(f"❌ Error scraping OCC jobs for {skill}: {e}")
            return []

    async def scrape_occ_job_detail(
        self,
        job_id: str,
    ) -> Optional[JobPostingMinimal]:
        """
        Fetches detailed information for specific OCC job.
        
        Args:
            job_id: OCC job ID
        
        Returns:
            JobPostingMinimal or None if not found
            
        Example:
            job = await worker.scrape_occ_job_detail("OCC-12345")
        """
        try:
            # Lazy load OCCScraper if needed
            if self._occ_scraper is None:
                from app.services.occ_scraper_service import OCCScraper
                self._occ_scraper = OCCScraper()
            
            async with self._occ_scraper as scraper:
                offer = await scraper.fetch_job_detail(job_id)
            
            if not offer:
                return None
            
            return JobPostingMinimal(
                external_job_id=offer.job_id,
                title=offer.title,
                company=offer.company,
                location=offer.location,
                description=offer.description or offer.full_description or "No description",
                skills=offer.skills or [],
                work_mode=offer.work_mode,
                job_type=offer.job_type,
                published_at=offer.publication_date or datetime.now(),
            )
            
        except Exception as e:
            print(f"❌ Error fetching OCC job detail {job_id}: {e}")
            return None

    async def scrape_occ_batch(
        self,
        skill_location_pairs: List[tuple],
        limit_per_pair: int = 20,
    ) -> JobScraperResult:
        """
        Batch scrapes multiple skill/location combinations.
        Useful for initial load or full catalog updates.
        
        Args:
            skill_location_pairs: [("python", "mexico-city"), ("javascript", "remote"), ...]
            limit_per_pair: Jobs to fetch per combination
        
        Returns:
            JobScraperResult with aggregated results
            
        Example:
            pairs = [("python", "remote"), ("javascript", "mexico-city")]
            result = await worker.scrape_occ_batch(pairs, limit_per_pair=20)
        """
        import time
        
        start_time = time.time()
        all_jobs = []
        duplicate_count = 0
        
        for skill, location in skill_location_pairs:
            try:
                jobs = await self.scrape_occ_jobs_by_skill(
                    skill=skill,
                    location=location,
                    limit=limit_per_pair,
                )
                
                # Deduplicate and add
                unique_jobs, dupes = await self.deduplicate_jobs(jobs)
                all_jobs.extend(unique_jobs)
                duplicate_count += dupes
                
                # Respect rate limiting
                await asyncio.sleep(1.5)
                
            except Exception as e:
                print(f"⚠️  Error in batch for {skill}/{location}: {e}")
                continue
        
        execution_time = time.time() - start_time
        
        return JobScraperResult(
            query="batch_occ_scrape",
            total_found=len(all_jobs) + duplicate_count,
            jobs=all_jobs,
            duplicates_removed=duplicate_count,
            execution_time_ms=execution_time * 1000,
        )


# ============================================================================
# Service Functions
# ============================================================================

async def scrape_jobs_service(
    keyword: str,
    location: Optional[str] = None,
    limit: int = 20
) -> JobScraperResult:
    """
    Service function to scrape jobs with deduplication.
    
    This is the main entry point for job scraping.
    
    Args:
        keyword: Search keyword
        location: Optional location filter
        limit: Max results to return
        
    Returns:
        JobScraperResult with jobs and metrics
        
    Example:
        result = await scrape_jobs_service("Python", "Remote", limit=20)
        print(f"Found {len(result.jobs)} jobs")
    """
    start_time = datetime.now()
    
    try:
        # Initialize worker
        worker = JobScraperWorker()
        
        # Search jobs
        jobs = await worker.search_jobs(keyword, location, limit)
        
        # Deduplicate
        unique_jobs, duplicates = await worker.deduplicate_jobs(jobs)
        
        # Calculate execution time
        elapsed_ms = (datetime.now() - start_time).total_seconds() * 1000
        
        return JobScraperResult(
            query=f"{keyword}" + (f" {location}" if location else ""),
            total_found=len(unique_jobs),
            jobs=unique_jobs,
            duplicates_removed=duplicates,
            execution_time_ms=elapsed_ms
        )
        
    except Exception as e:
        print(f"❌ Scraping error: {str(e)}")
        return JobScraperResult(
            query=keyword,
            total_found=0,
            jobs=[],
            duplicates_removed=0,
            execution_time_ms=(datetime.now() - start_time).total_seconds() * 1000
        )


# ============================================================================
# Batch Processing
# ============================================================================

async def scrape_jobs_batch(
    queries: List[JobSearchQuery],
    concurrent_tasks: int = 3
) -> List[JobScraperResult]:
    """
    Scrape multiple job searches concurrently.
    
    Args:
        queries: List of search queries
        concurrent_tasks: Max concurrent scraping tasks
        
    Returns:
        List of results from all queries
        
    Note:
        Uses semaphore to limit concurrent tasks and avoid overwhelming
        the target website.
    """
    semaphore = asyncio.Semaphore(concurrent_tasks)
    
    async def scrape_with_semaphore(query: JobSearchQuery):
        async with semaphore:
            return await scrape_jobs_service(
                query.keyword,
                query.location,
                query.limit
            )
    
    tasks = [scrape_with_semaphore(q) for q in queries]
    results = await asyncio.gather(*tasks, return_exceptions=False)
    
    return results
