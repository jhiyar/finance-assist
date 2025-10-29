"""
Confluence Service for fetching and processing Confluence pages
"""

import os
import requests
import logging
from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ConfluenceService:
    """Service for fetching and processing Confluence pages"""
    
    def __init__(self):
        self.base_url = os.getenv("CONFLUENCE_BASE_URL", "https://phoebussoftware.atlassian.net/wiki")
        self.api_url = f"{self.base_url}/rest/api"
        self.auth = (
            os.getenv("CONFLUENCE_USERNAME", "sze@phoebussoftware.com"),
            os.getenv("CONFLUENCE_API_TOKEN", "")
        )
        logger.info(f"ConfluenceService initialized with base URL: {self.base_url}")

    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None, data: Optional[Dict] = None) -> Optional[Dict]:
        """Make a request to the Confluence API"""
        url = f"{self.api_url}{endpoint}"
        try:
            response = requests.request(method, url, params=params, json=data, auth=self.auth, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Confluence API request failed for {url}: {e}")
            return None

    def get_child_pages(self, parent_id: str) -> List[Dict]:
        """Get child pages of a parent page"""
        endpoint = f"/content/{parent_id}/child/page"
        params = {"limit": 200}  # Increase limit to fetch more children
        data = self._make_request("GET", endpoint, params=params)
        return data.get("results", []) if data else []

    def get_page_content(self, page_id: str) -> Optional[Dict]:
        """Get full page content and metadata for a given page ID"""
        endpoint = f"/content/{page_id}"
        params = {"expand": "body.storage,version,space,ancestors,history"}
        data = self._make_request("GET", endpoint, params=params)
        return data if data else None

    def clean_html_content(self, html_content: str) -> str:
        """Extracts clean text from HTML content"""
        if not html_content:
            return ""
        soup = BeautifulSoup(html_content, 'html.parser')
        # Remove script and style elements
        for script_or_style in soup(["script", "style"]):
            script_or_style.extract()
        text = soup.get_text()
        # Break into lines and remove leading/trailing whitespace on each line
        lines = (line.strip() for line in text.splitlines())
        # Break multi-headlines into a line each
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        # Drop blank lines
        text = ' '.join(chunk for chunk in chunks if chunk)
        return text

    def get_all_pages_recursive(self, parent_id: str, visited: Optional[set] = None, progress_callback: Optional[callable] = None) -> List[Dict[str, Any]]:
        """Recursively fetch all pages starting from a parent page"""
        if visited is None:
            visited = set()
        
        if parent_id in visited:
            return []
        
        visited.add(parent_id)
        all_pages = []
        
        try:
            # Get child pages
            child_pages = self.get_child_pages(parent_id)
            logger.info(f"Found {len(child_pages)} child pages for parent {parent_id}")
            
            for i, page in enumerate(child_pages):
                page_id = page["id"]
                page_title = page.get("title", f"Page {page_id}")
                
                # Call progress callback if provided
                if progress_callback:
                    progress_callback(i + 1, len(child_pages), page_title)
                
                # Get full page content
                page_data = self.get_page_content(page_id)
                if not page_data:
                    continue
                
                # Extract and clean content
                html_content = page_data.get("body", {}).get("storage", {}).get("value", "")
                clean_content = self.clean_html_content(html_content)
                
                # Prepare page data
                page_info = {
                    "id": page_id,
                    "title": page_data.get("title", ""),
                    "content": clean_content,
                    "html_content": html_content,
                    "space_key": page_data.get("space", {}).get("key", ""),
                    "space_name": page_data.get("space", {}).get("name", ""),
                    "version": page_data.get("version", {}).get("number", 1),
                    "created": page_data.get("history", {}).get("createdDate", ""),  # Use history.createdDate
                    "last_modified": page_data.get("version", {}).get("when", ""),
                    "url": f"{self.base_url}/pages/viewpage.action?pageId={page_id}",
                    "ancestors": [ancestor.get("title", "") for ancestor in page_data.get("ancestors", [])],
                    "parent_id": parent_id
                }
                
                all_pages.append(page_info)
                logger.info(f"Processed page: {page_info['title']} (ID: {page_id})")
                
                # Recursively get child pages
                child_pages_recursive = self.get_all_pages_recursive(page_id, visited, progress_callback)
                all_pages.extend(child_pages_recursive)
                
        except Exception as e:
            logger.error(f"Error processing parent page {parent_id}: {e}")
        
        return all_pages

    def fetch_confluence_documents(self, parent_id: str = "27394188", progress_callback: Optional[callable] = None) -> Dict[str, Any]:
        """Fetch all Confluence documents from a parent page"""
        logger.info(f"Starting Confluence document fetch from parent ID: {parent_id}")
        
        try:
            pages = self.get_all_pages_recursive(parent_id, progress_callback=progress_callback)
            
            result = {
                "success": True,
                "total_pages": len(pages),
                "pages": pages,
                "fetched_at": datetime.now().isoformat(),
                "parent_id": parent_id
            }
            
            logger.info(f"Successfully fetched {len(pages)} pages from Confluence")
            return result
            
        except Exception as e:
            logger.error(f"Error fetching Confluence documents: {e}")
            return {
                "success": False,
                "error": str(e),
                "total_pages": 0,
                "pages": [],
                "fetched_at": datetime.now().isoformat(),
                "parent_id": parent_id
            }


def get_confluence_service() -> ConfluenceService:
    """Get a Confluence service instance"""
    return ConfluenceService()
