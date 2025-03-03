from typing import Dict, Any, Optional
import aiohttp
from bs4 import BeautifulSoup
import trafilatura
from datetime import datetime
import hashlib
from urllib.parse import urlparse
import re

class URLExtractor:
    def __init__(self):
        self.session = None
        self.article_indicators = {
            'selectors': [
                'article', '.article', '#article',
                '[type="article"]', '[itemtype*="Article"]'
            ],
            'url_patterns': [
                r'/article/', r'/news/', r'/story/', 
                r'/\d{4}/\d{2}/\d{2}/', r'/blog/'
            ]
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def extract(self, url: str) -> Dict[str, Any]:
        """Extract and analyze content from URL"""
        try:
            async with self.session.get(url) as response:
                html = await response.text()
                
            # Use trafilatura for main content extraction
            content = trafilatura.extract(html)
            soup = BeautifulSoup(html, 'html.parser')
            
            return {
                "url": url,
                "domain": urlparse(url).netloc,
                "content": content,
                "metadata": await self._extract_metadata(soup, url),
                "content_hash": self._generate_content_hash(content),
                "is_article": await self._is_article(soup, url),
                "extracted_at": datetime.utcnow().isoformat()
            }
            
    async def _extract_metadata(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Extract metadata from the page"""
        return {
            "title": self._get_title(soup),
            "description": self._get_description(soup),
            "published_date": self._get_date(soup),
            "author": self._get_author(soup),
            "canonical_url": self._get_canonical_url(soup, url)
        }
        
    def _generate_content_hash(self, content: str) -> str:
        """Generate a unique hash for the content"""
        return hashlib.sha256(content.encode()).hexdigest()
        
    async def _is_article(self, soup: BeautifulSoup, url: str) -> bool:
        """Determine if the URL points to an article"""
        # Check URL patterns
        if any(re.search(pattern, url) for pattern in self.article_indicators['url_patterns']):
            return True
            
        # Check HTML structure
        return any(soup.select(selector) for selector in self.article_indicators['selectors'])
        
    def _get_title(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article title"""
        title = soup.find('meta', property='og:title')
        if title:
            return title.get('content')
        return soup.title.string if soup.title else None
        
    def _get_description(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract article description"""
        desc = soup.find('meta', property='og:description')
        if desc:
            return desc.get('content')
        desc = soup.find('meta', attrs={'name': 'description'})
        return desc.get('content') if desc else None
        
    def _get_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date"""
        for date_meta in [
            ('meta', 'property', 'article:published_time'),
            ('meta', 'property', 'og:published_time'),
            ('time', 'datetime', None),
        ]:
            element = soup.find(date_meta[0], {date_meta[1]: date_meta[2]})
            if element:
                return element.get('datetime') or element.get('content')
        return None
        
    def _get_author(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract author information"""
        for author_meta in [
            ('meta', 'property', 'article:author'),
            ('meta', 'name', 'author'),
            ('a', 'rel', 'author'),
        ]:
            element = soup.find(author_meta[0], {author_meta[1]: author_meta[2]})
            if element:
                return element.get('content') or element.text.strip()
        return None
        
    def _get_canonical_url(self, soup: BeautifulSoup, url: str) -> str:
        """Get canonical URL if available"""
        canonical = soup.find('link', rel='canonical')
        return canonical.get('href') if canonical else url 