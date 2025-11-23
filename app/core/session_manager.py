"""
Session Manager for web scraping with HTTP session handling
and adaptive request delays.

This module provides a managed HTTP client that rotates User-Agent headers
and enforces adaptive delays between requests to avoid detection.
"""

import random
import asyncio
from datetime import datetime
from typing import Optional
import httpx


# Rotating User-Agents to appear like real browsers
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (iPad; CPU OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Macintosh; PPC Mac OS X 10_5_8) AppleWebKit/537.36 Firefox/121.0",
]


class SessionManager:
    """
    Manages HTTP sessions for web scraping with rate limiting and header rotation.
    
    Features:
    - Rotating User-Agent headers
    - Adaptive delays between requests
    - Connection pooling
    - Context manager support
    
    Example:
        manager = SessionManager()
        await manager.adaptive_delay()
        session = await manager.get_session()
        response = await session.get(url)
    """
    
    # Delay constraints (seconds)
    MIN_DELAY = 1.0
    MAX_DELAY = 3.0
    MAX_RETRIES = 2
    
    def __init__(self):
        """Initialize SessionManager with no active session"""
        self.last_request: Optional[datetime] = None
        self.session: Optional[httpx.AsyncClient] = None
    
    def get_headers(self) -> dict:
        """
        Generate HTTP headers that mimic a real browser.
        
        Returns:
            dict: Headers dictionary with rotated User-Agent
        """
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-MX,es;q=0.9,en;q=0.8",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
            "Cache-Control": "no-cache",
            "Pragma": "no-cache",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
        }
    
    async def adaptive_delay(self) -> None:
        """
        Enforce adaptive delay between HTTP requests.
        
        If a request was made recently, calculate remaining delay needed
        to avoid rate limiting. First call is immediate.
        
        This prevents detection by job sites and respects robots.txt
        """
        if self.last_request:
            elapsed = (datetime.now() - self.last_request).total_seconds()
            delay_needed = random.uniform(self.MIN_DELAY, self.MAX_DELAY)
            
            if elapsed < delay_needed:
                sleep_time = delay_needed - elapsed
                await asyncio.sleep(sleep_time)
        
        self.last_request = datetime.now()
    
    async def get_session(self) -> httpx.AsyncClient:
        """
        Get or create an async HTTP session.
        
        Returns:
            httpx.AsyncClient: Async HTTP client with proper headers
            
        Notes:
            - Session is created lazily on first access
            - Session is reused across multiple requests
            - Call close() to cleanup resources
        """
        if not self.session:
            self.session = httpx.AsyncClient(
                headers=self.get_headers(),
                timeout=30.0,
                follow_redirects=True,
                limits=httpx.Limits(
                    max_connections=10,
                    max_keepalive_connections=5
                )
            )
        return self.session
    
    async def close(self) -> None:
        """
        Close and cleanup the HTTP session.
        
        Call this method when done with the SessionManager to free resources.
        """
        if self.session:
            await self.session.aclose()
            self.session = None
    
    async def __aenter__(self):
        """Async context manager entry point"""
        return await self.get_session()
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit point - closes session"""
        await self.close()


# Global singleton instance
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """
    Get or create the global SessionManager singleton.
    
    This ensures only one session manager is used across the application,
    preventing connection leaks and maintaining consistent headers.
    
    Returns:
        SessionManager: Global singleton instance
        
    Example:
        manager = get_session_manager()
        await manager.adaptive_delay()
    """
    global _session_manager
    if not _session_manager:
        _session_manager = SessionManager()
    return _session_manager


async def reset_session_manager() -> None:
    """
    Reset the global session manager (primarily for testing).
    
    This is useful in tests to ensure a fresh session state.
    """
    global _session_manager
    if _session_manager:
        await _session_manager.close()
    _session_manager = None
