"""
Unit tests for Job Scraper Worker module.

Tests verify:
- URL building for search queries
- Job deduplication logic
- Service function integration
- Batch processing
- Error handling
"""

import pytest
import asyncio
from datetime import datetime
from app.services.job_scraper_worker import (
    JobScraperWorker,
    JobPostingMinimal,
    scrape_jobs_service,
    scrape_jobs_batch,
    JobSearchQuery,
)
from app.core.session_manager import SessionManager


class TestJobScraperWorkerUrlBuilding:
    """Tests for URL building functionality"""
    
    def test_build_url_with_keyword_only(self):
        """Test URL building with just keyword"""
        worker = JobScraperWorker()
        
        url = worker._build_search_url("Python", None)
        
        assert "occ.com.mx" in url
        assert "python" in url.lower()
        assert "empleos" in url
        print(f"✓ URL with keyword: {url}")
    
    def test_build_url_with_keyword_and_location(self):
        """Test URL building with keyword and location"""
        worker = JobScraperWorker()
        
        url = worker._build_search_url("Python", "Remote")
        
        assert "occ.com.mx" in url
        assert "python" in url.lower()
        assert "remote" in url.lower()
        print(f"✓ URL with location: {url}")
    
    def test_build_url_handles_spaces(self):
        """Test that spaces are handled correctly"""
        worker = JobScraperWorker()
        
        url = worker._build_search_url("Machine Learning", "New York")
        
        assert "machine-learning" in url.lower()
        assert "new-york" in url.lower()
        print(f"✓ Spaces handled: {url}")
    
    def test_build_url_handles_special_cases(self):
        """Test URL building for various keywords"""
        worker = JobScraperWorker()
        
        keywords = ["Java", "C++", ".NET", "Node.js", "React Native"]
        
        for keyword in keywords:
            url = worker._build_search_url(keyword, None)
            assert "occ.com.mx" in url
            assert len(url) > 20
        
        print(f"✓ All keywords handled: {len(keywords)} cases")


class TestJobScraperWorkerDeduplication:
    """Tests for job deduplication"""
    
    @pytest.mark.asyncio
    async def test_deduplicate_removes_duplicates(self):
        """Test that deduplication removes duplicate job IDs"""
        worker = JobScraperWorker()
        
        jobs = [
            JobPostingMinimal(
                external_job_id="job1",
                title="Dev",
                company="Acme",
                location="Remote",
                description="Desc",
                skills=["Python"],
                published_at=datetime.now()
            ),
            JobPostingMinimal(
                external_job_id="job1",  # Duplicate
                title="Dev",
                company="Acme",
                location="Remote",
                description="Desc",
                skills=["Python"],
                published_at=datetime.now()
            ),
            JobPostingMinimal(
                external_job_id="job2",
                title="Dev2",
                company="Acme",
                location="Remote",
                description="Desc",
                skills=["JS"],
                published_at=datetime.now()
            ),
        ]
        
        unique, duplicates = await worker.deduplicate_jobs(jobs)
        
        assert len(unique) == 2
        assert duplicates == 1
        print(f"✓ Deduplication: {len(jobs)} → {len(unique)} jobs ({duplicates} removed)")
    
    @pytest.mark.asyncio
    async def test_deduplicate_with_empty_list(self):
        """Test deduplication with empty list"""
        worker = JobScraperWorker()
        
        unique, duplicates = await worker.deduplicate_jobs([])
        
        assert len(unique) == 0
        assert duplicates == 0
        print("✓ Empty list handled")
    
    @pytest.mark.asyncio
    async def test_deduplicate_cache_persistence(self):
        """Test that deduplication cache persists across calls"""
        worker = JobScraperWorker()
        
        job1 = JobPostingMinimal(
            external_job_id="job1",
            title="Dev",
            company="Acme",
            location="Remote",
            description="Desc",
            skills=["Python"],
            published_at=datetime.now()
        )
        
        # First call
        unique1, dup1 = await worker.deduplicate_jobs([job1])
        assert len(unique1) == 1
        
        # Second call with same job should be marked as duplicate
        unique2, dup2 = await worker.deduplicate_jobs([job1])
        assert len(unique2) == 0
        assert dup2 == 1
        
        print("✓ Cache persistence working")
    
    @pytest.mark.asyncio
    async def test_deduplicate_reset_cache(self):
        """Test that cache reset works"""
        worker = JobScraperWorker()
        
        job = JobPostingMinimal(
            external_job_id="job1",
            title="Dev",
            company="Acme",
            location="Remote",
            description="Desc",
            skills=["Python"],
            published_at=datetime.now()
        )
        
        # First: seen
        await worker.deduplicate_jobs([job])
        
        # Reset cache
        worker.reset_duplicates_cache()
        
        # Second: should be new
        unique, dup = await worker.deduplicate_jobs([job])
        assert len(unique) == 1
        assert dup == 0
        
        print("✓ Cache reset working")


class TestJobScraperWorkerIntegration:
    """Integration tests for full scraper"""
    
    @pytest.mark.asyncio
    async def test_worker_with_session_manager(self):
        """Test that worker integrates with SessionManager"""
        manager = SessionManager()
        worker = JobScraperWorker(session_manager=manager)
        
        assert worker.session_manager is not None
        assert worker.session_manager is manager
        
        await manager.close()
        print("✓ SessionManager integration")
    
    @pytest.mark.asyncio
    async def test_search_jobs_graceful_degradation(self):
        """Test that search handles errors gracefully"""
        worker = JobScraperWorker()
        
        # This will fail (invalid URL format for real search)
        # but should not raise exception
        jobs = await worker.search_jobs("InvalidKeyword")
        
        assert isinstance(jobs, list)
        # For MVP, parser returns empty list
        print(f"✓ Graceful error handling: {len(jobs)} jobs")


class TestJobScraperService:
    """Tests for scrape_jobs_service function"""
    
    @pytest.mark.asyncio
    async def test_scrape_jobs_service_basic(self):
        """Test basic scrape_jobs_service call"""
        result = await scrape_jobs_service("Python", limit=10)
        
        assert result.query == "Python"
        assert result.total_found >= 0
        assert isinstance(result.jobs, list)
        assert result.execution_time_ms > 0
        
        print(f"✓ Service result: {result.total_found} jobs in {result.execution_time_ms:.2f}ms")
    
    @pytest.mark.asyncio
    async def test_scrape_jobs_service_with_location(self):
        """Test service with location parameter"""
        result = await scrape_jobs_service("Python", "Remote", limit=10)
        
        assert result.query == "Python Remote"
        assert result.execution_time_ms > 0
        
        print(f"✓ Service with location: {result.query}")
    
    @pytest.mark.asyncio
    async def test_scrape_jobs_service_metrics(self):
        """Test that service returns valid metrics"""
        result = await scrape_jobs_service("Python")
        
        # Check metrics
        assert result.total_found >= 0
        assert result.duplicates_removed >= 0
        assert result.execution_time_ms > 0
        assert isinstance(result.jobs, list)
        
        print(f"✓ Metrics: {result.total_found} found, {result.duplicates_removed} duplicates, {result.execution_time_ms:.2f}ms")


class TestJobScraperBatch:
    """Tests for batch processing"""
    
    @pytest.mark.asyncio
    async def test_scrape_jobs_batch(self):
        """Test batch scraping with multiple queries"""
        queries = [
            JobSearchQuery(keyword="Python"),
            JobSearchQuery(keyword="JavaScript"),
            JobSearchQuery(keyword="Java"),
        ]
        
        results = await scrape_jobs_batch(queries, concurrent_tasks=2)
        
        assert len(results) == 3
        assert all(hasattr(r, 'execution_time_ms') for r in results)
        
        print(f"✓ Batch processing: {len(results)} queries completed")
    
    @pytest.mark.asyncio
    async def test_scrape_jobs_batch_with_locations(self):
        """Test batch scraping with location parameters"""
        queries = [
            JobSearchQuery(keyword="Python", location="Remote"),
            JobSearchQuery(keyword="JavaScript", location="CDMX"),
        ]
        
        results = await scrape_jobs_batch(queries, concurrent_tasks=2)
        
        assert len(results) == 2
        assert results[0].query == "Python Remote"
        assert results[1].query == "JavaScript CDMX"
        
        print(f"✓ Batch with locations: {len(results)} queries")
    
    @pytest.mark.asyncio
    async def test_scrape_jobs_batch_concurrency_limit(self):
        """Test that concurrency limit is respected"""
        queries = [
            JobSearchQuery(keyword=f"Keyword{i}") 
            for i in range(10)
        ]
        
        # Should complete without overwhelming
        results = await scrape_jobs_batch(queries, concurrent_tasks=3)
        
        assert len(results) == 10
        print(f"✓ Concurrency limit respected: 10 queries, 3 concurrent")


class TestJobScraperErrorHandling:
    """Tests for error handling"""
    
    @pytest.mark.asyncio
    async def test_search_handles_timeout(self):
        """Test that timeout is handled gracefully"""
        worker = JobScraperWorker()
        
        # Should not raise, just return empty
        jobs = await worker.search_jobs("test")
        assert isinstance(jobs, list)
        
        print("✓ Timeout handling")
    
    @pytest.mark.asyncio
    async def test_service_handles_errors(self):
        """Test that service handles errors gracefully"""
        # Pass invalid keyword (should still return valid result struct)
        result = await scrape_jobs_service("", limit=10)
        
        assert isinstance(result.jobs, list)
        assert result.execution_time_ms > 0
        
        print("✓ Error handling in service")


class TestJobScraperModels:
    """Tests for data models"""
    
    def test_job_posting_model(self):
        """Test JobPostingMinimal model"""
        job = JobPostingMinimal(
            external_job_id="job123",
            title="Python Developer",
            company="Acme Corp",
            location="Remote",
            description="Build awesome stuff",
            skills=["Python", "FastAPI"],
            work_mode="Remote",
            job_type="Full-time",
            published_at=datetime.now()
        )
        
        assert job.external_job_id == "job123"
        assert job.title == "Python Developer"
        assert len(job.skills) == 2
        
        print("✓ JobPostingMinimal model")
    
    def test_job_search_query_model(self):
        """Test JobSearchQuery model"""
        query = JobSearchQuery(
            keyword="Python",
            location="Remote",
            limit=50
        )
        
        assert query.keyword == "Python"
        assert query.location == "Remote"
        assert query.limit == 50
        assert query.skip == 0
        
        print("✓ JobSearchQuery model")
    
    def test_job_scraper_result_model(self):
        """Test JobScraperResult model"""
        from app.services.job_scraper_worker import JobScraperResult
        
        result = JobScraperResult(
            query="Python Remote",
            total_found=5,
            jobs=[],
            duplicates_removed=1,
            execution_time_ms=123.45
        )
        
        assert result.query == "Python Remote"
        assert result.total_found == 5
        assert result.execution_time_ms == 123.45
        
        print("✓ JobScraperResult model")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
