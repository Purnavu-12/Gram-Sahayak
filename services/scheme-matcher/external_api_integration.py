"""
External API Integration Module
Validates: Requirement 3.4 - Integration with myScheme API and e-Shram platform

This module provides integration with government scheme APIs to fetch
real-time scheme data and updates.
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
import logging
import asyncio

try:
    import aiohttp
    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

logger = logging.getLogger(__name__)


class ExternalAPIIntegration:
    """
    Integration with external government scheme APIs
    - myScheme API: Central government scheme portal
    - e-Shram API: Unorganized workers database
    """

    def __init__(
        self,
        myscheme_api_url: Optional[str] = None,
        eshram_api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: int = 30
    ):
        self.myscheme_api_url = myscheme_api_url or "https://api.myscheme.gov.in/v1"
        self.eshram_api_url = eshram_api_url or "https://api.eshram.gov.in/v1"
        self.api_key = api_key
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if not AIOHTTP_AVAILABLE:
            raise RuntimeError("aiohttp is not installed. Install with: pip install aiohttp")
        
        if self.session is None or self.session.closed:
            headers = {}
            if self.api_key:
                headers["Authorization"] = f"Bearer {self.api_key}"
            headers["Content-Type"] = "application/json"
            
            self.session = aiohttp.ClientSession(
                headers=headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self.session

    async def fetch_schemes_from_myscheme(
        self,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch schemes from myScheme API
        
        Args:
            filters: Optional filters for scheme search (category, state, etc.)
            
        Returns:
            List of scheme data from myScheme API
        """
        try:
            session = await self._get_session()
            url = f"{self.myscheme_api_url}/schemes"
            
            params = filters or {}
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    schemes = self._transform_myscheme_data(data)
                    logger.info(f"Fetched {len(schemes)} schemes from myScheme API")
                    return schemes
                else:
                    logger.error(f"myScheme API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching from myScheme API: {e}")
            return []

    async def fetch_worker_schemes_from_eshram(
        self,
        occupation_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch worker-specific schemes from e-Shram API
        
        Args:
            occupation_type: Type of unorganized worker occupation
            
        Returns:
            List of scheme data from e-Shram API
        """
        try:
            session = await self._get_session()
            url = f"{self.eshram_api_url}/schemes"
            
            params = {}
            if occupation_type:
                params["occupation"] = occupation_type
            
            async with session.get(url, params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    schemes = self._transform_eshram_data(data)
                    logger.info(f"Fetched {len(schemes)} schemes from e-Shram API")
                    return schemes
                else:
                    logger.error(f"e-Shram API error: {response.status}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error fetching from e-Shram API: {e}")
            return []

    async def fetch_scheme_updates(
        self,
        since: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Fetch scheme updates from both APIs since a given timestamp
        
        Args:
            since: Fetch updates since this datetime (default: last 24 hours)
            
        Returns:
            List of scheme updates
        """
        if since is None:
            # Default to last 24 hours
            from datetime import timedelta
            since = datetime.now() - timedelta(hours=24)
        
        # Fetch from both APIs in parallel
        myscheme_task = self.fetch_schemes_from_myscheme(
            filters={"updated_since": since.isoformat()}
        )
        eshram_task = self.fetch_worker_schemes_from_eshram()
        
        myscheme_schemes, eshram_schemes = await asyncio.gather(
            myscheme_task,
            eshram_task,
            return_exceptions=True
        )
        
        # Handle exceptions
        if isinstance(myscheme_schemes, Exception):
            logger.error(f"myScheme fetch failed: {myscheme_schemes}")
            myscheme_schemes = []
        if isinstance(eshram_schemes, Exception):
            logger.error(f"e-Shram fetch failed: {eshram_schemes}")
            eshram_schemes = []
        
        # Combine and deduplicate
        all_schemes = myscheme_schemes + eshram_schemes
        unique_schemes = self._deduplicate_schemes(all_schemes)
        
        logger.info(f"Fetched {len(unique_schemes)} unique scheme updates")
        return unique_schemes

    def _transform_myscheme_data(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform myScheme API response to internal format"""
        schemes = []
        
        # Handle different response formats
        scheme_list = api_data.get("schemes", api_data.get("data", []))
        
        for item in scheme_list:
            scheme = {
                "scheme_id": item.get("id", item.get("scheme_id")),
                "name": item.get("name", item.get("scheme_name")),
                "description": item.get("description", ""),
                "eligibility": self._parse_eligibility(item.get("eligibility", {})),
                "benefit_amount": item.get("benefit_amount", 0),
                "difficulty": self._map_difficulty(item.get("complexity", "medium")),
                "category": item.get("category", "general"),
                "related_schemes": item.get("related_schemes", []),
                "last_updated": item.get("updated_at", datetime.now().isoformat()),
                "source": "myScheme"
            }
            schemes.append(scheme)
        
        return schemes

    def _transform_eshram_data(self, api_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Transform e-Shram API response to internal format"""
        schemes = []
        
        # Handle different response formats
        scheme_list = api_data.get("schemes", api_data.get("data", []))
        
        for item in scheme_list:
            scheme = {
                "scheme_id": item.get("id", item.get("scheme_id")),
                "name": item.get("name", item.get("scheme_name")),
                "description": item.get("description", ""),
                "eligibility": self._parse_eligibility(item.get("eligibility", {})),
                "benefit_amount": item.get("benefit_amount", 0),
                "difficulty": self._map_difficulty(item.get("complexity", "medium")),
                "category": "employment",  # e-Shram focuses on worker schemes
                "related_schemes": item.get("related_schemes", []),
                "last_updated": item.get("updated_at", datetime.now().isoformat()),
                "source": "e-Shram"
            }
            schemes.append(scheme)
        
        return schemes

    def _parse_eligibility(self, eligibility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Parse eligibility criteria from API format to internal format"""
        parsed = {}
        
        # Map common fields
        field_mapping = {
            "occupation": "occupation",
            "occupations": "occupation",
            "age_min": "min_age",
            "age_max": "max_age",
            "income_max": "max_income",
            "gender": "gender",
            "caste": "caste",
            "state": "state",
            "states": "state"
        }
        
        for api_field, internal_field in field_mapping.items():
            if api_field in eligibility_data:
                value = eligibility_data[api_field]
                # Ensure lists are lists
                if internal_field in ["occupation", "gender", "caste", "state"]:
                    if not isinstance(value, list):
                        value = [value]
                parsed[internal_field] = value
        
        return parsed

    def _map_difficulty(self, complexity: str) -> str:
        """Map API complexity values to internal difficulty levels"""
        mapping = {
            "simple": "easy",
            "easy": "easy",
            "moderate": "medium",
            "medium": "medium",
            "complex": "hard",
            "hard": "hard"
        }
        return mapping.get(complexity.lower(), "medium")

    def _deduplicate_schemes(self, schemes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate schemes based on scheme_id"""
        seen = {}
        for scheme in schemes:
            scheme_id = scheme.get("scheme_id")
            if scheme_id:
                # Keep the most recently updated version
                if scheme_id not in seen:
                    seen[scheme_id] = scheme
                else:
                    existing_updated = seen[scheme_id].get("last_updated", "")
                    new_updated = scheme.get("last_updated", "")
                    if new_updated > existing_updated:
                        seen[scheme_id] = scheme
        
        return list(seen.values())

    async def close(self):
        """Close the aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def __aenter__(self):
        """Async context manager entry"""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
