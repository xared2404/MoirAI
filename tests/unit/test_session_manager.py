"""
Unit tests for SessionManager module.

Tests verify:
- User-Agent rotation
- Adaptive delay timing
- Session creation and cleanup
- HTTP headers validity
"""

import pytest
import asyncio
from datetime import datetime
from app.core.session_manager import (
    SessionManager,
    get_session_manager,
    reset_session_manager,
)


class TestSessionManagerUserAgent:
    """Tests for User-Agent rotation functionality"""
    
    def test_get_headers_contains_user_agent(self):
        """Verify headers include User-Agent field"""
        manager = SessionManager()
        headers = manager.get_headers()
        
        assert "User-Agent" in headers
        assert len(headers["User-Agent"]) > 0
    
    def test_user_agent_rotation(self):
        """Verify User-Agent changes across calls"""
        manager = SessionManager()
        
        user_agents = set()
        for _ in range(10):
            headers = manager.get_headers()
            user_agents.add(headers["User-Agent"])
        
        # Should have multiple different User-Agents
        assert len(user_agents) > 1
        print(f"✓ Detected {len(user_agents)} different User-Agents")
    
    def test_headers_validity(self):
        """Verify all headers are valid"""
        manager = SessionManager()
        headers = manager.get_headers()
        
        required_headers = [
            "User-Agent",
            "Accept",
            "Accept-Language",
            "Accept-Encoding",
            "Connection",
        ]
        
        for header in required_headers:
            assert header in headers, f"Missing header: {header}"
            assert len(headers[header]) > 0, f"Empty header: {header}"
        
        print("✓ All required headers present and non-empty")


class TestSessionManagerDelay:
    """Tests for adaptive delay functionality"""
    
    @pytest.mark.asyncio
    async def test_first_delay_is_fast(self):
        """First delay call should be immediate"""
        manager = SessionManager()
        
        start = datetime.now()
        await manager.adaptive_delay()
        elapsed = (datetime.now() - start).total_seconds()
        
        # Should be nearly instant (< 100ms)
        assert elapsed < 0.1
        print(f"✓ First delay was fast: {elapsed:.4f}s")
    
    @pytest.mark.asyncio
    async def test_second_delay_waits(self):
        """Second delay call should enforce minimum delay"""
        manager = SessionManager()
        
        # First delay
        await manager.adaptive_delay()
        
        # Second delay should wait
        start = datetime.now()
        await manager.adaptive_delay()
        elapsed = (datetime.now() - start).total_seconds()
        
        # Should be at least MIN_DELAY
        assert elapsed >= manager.MIN_DELAY - 0.2  # Small margin for timing variance
        # Should be at most MAX_DELAY
        assert elapsed <= manager.MAX_DELAY + 0.2
        
        print(f"✓ Second delay waited: {elapsed:.2f}s (range: {manager.MIN_DELAY}-{manager.MAX_DELAY}s)")
    
    @pytest.mark.asyncio
    async def test_adaptive_delay_timestamps(self):
        """Verify last_request timestamp is updated"""
        manager = SessionManager()
        
        assert manager.last_request is None
        
        await manager.adaptive_delay()
        first_time = manager.last_request
        assert first_time is not None
        
        await asyncio.sleep(0.5)
        await manager.adaptive_delay()
        second_time = manager.last_request
        
        # Timestamps should be different
        assert second_time > first_time
        print("✓ Timestamps updated correctly")


class TestSessionManagerSession:
    """Tests for HTTP session creation and management"""
    
    @pytest.mark.asyncio
    async def test_get_session_creates_client(self):
        """Verify get_session creates an AsyncClient"""
        manager = SessionManager()
        
        session = await manager.get_session()
        assert session is not None
        assert hasattr(session, 'get')
        assert hasattr(session, 'post')
        
        await manager.close()
        print("✓ Session client created successfully")
    
    @pytest.mark.asyncio
    async def test_get_session_reuses_client(self):
        """Verify get_session returns same client on multiple calls"""
        manager = SessionManager()
        
        session1 = await manager.get_session()
        session2 = await manager.get_session()
        
        assert session1 is session2
        
        await manager.close()
        print("✓ Session is reused across calls")
    
    @pytest.mark.asyncio
    async def test_close_session(self):
        """Verify close properly cleans up session"""
        manager = SessionManager()
        
        session = await manager.get_session()
        assert manager.session is not None
        
        await manager.close()
        assert manager.session is None
        
        print("✓ Session closed and cleaned up")


class TestSessionManagerContext:
    """Tests for context manager functionality"""
    
    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Verify async context manager works"""
        manager = SessionManager()
        
        async with manager as session:
            assert session is not None
            assert hasattr(session, 'get')
        
        # After exiting, session should be closed
        assert manager.session is None
        print("✓ Context manager cleanup working")


class TestSessionManagerSingleton:
    """Tests for global singleton pattern"""
    
    @pytest.mark.asyncio
    async def test_singleton_instance(self):
        """Verify get_session_manager returns singleton"""
        await reset_session_manager()
        
        manager1 = get_session_manager()
        manager2 = get_session_manager()
        
        assert manager1 is manager2
        print("✓ Singleton pattern working")
    
    @pytest.mark.asyncio
    async def test_singleton_reset(self):
        """Verify reset_session_manager works"""
        manager1 = get_session_manager()
        
        await reset_session_manager()
        manager2 = get_session_manager()
        
        # Should be different instances
        assert manager1 is not manager2
        
        await reset_session_manager()
        print("✓ Singleton reset working")


class TestSessionManagerIntegration:
    """Integration tests combining multiple features"""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test realistic workflow with delays and headers"""
        manager = SessionManager()
        
        try:
            # Get initial headers
            headers1 = manager.get_headers()
            assert "User-Agent" in headers1
            
            # First delay (immediate)
            await manager.adaptive_delay()
            
            # Get session
            session = await manager.get_session()
            assert session is not None
            
            # More delays
            await manager.adaptive_delay()
            headers2 = manager.get_headers()
            
            # Verify we can get different headers
            assert "User-Agent" in headers2
            
            print("✓ Full workflow completed successfully")
        finally:
            await manager.close()
    
    @pytest.mark.asyncio
    async def test_consecutive_delays_timing(self):
        """Test that consecutive delays accumulate correctly"""
        manager = SessionManager()
        
        start_total = datetime.now()
        
        # Make 3 consecutive delays
        for i in range(3):
            await manager.adaptive_delay()
        
        total_elapsed = (datetime.now() - start_total).total_seconds()
        
        # First call is instant, next 2 should each be MIN_DELAY
        # So total should be roughly 2 * MIN_DELAY
        expected_min = 2 * manager.MIN_DELAY - 0.3
        
        assert total_elapsed >= expected_min
        print(f"✓ Three consecutive delays took {total_elapsed:.2f}s (expected min: {expected_min:.2f}s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
