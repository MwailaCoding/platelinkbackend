"""In-memory permission caching module."""
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional, Tuple

class PermissionCache:
    """Simple in-memory cache for user permissions."""
    
    def __init__(self, ttl_seconds: int = 300):
        self.cache: Dict[str, Tuple[List[str], datetime]] = {}
        self.ttl = ttl_seconds
    
    def get(self, user_id: str) -> Optional[List[str]]:
        """Get cached permissions for a user if still valid."""
        if user_id in self.cache:
            perms, timestamp = self.cache[user_id]
            if datetime.now(timezone.utc) - timestamp < timedelta(seconds=self.ttl):
                return perms
            else:
                del self.cache[user_id]
        return None
    
    def set(self, user_id: str, permissions: List[str]) -> None:
        """Cache permissions for a user."""
        self.cache[user_id] = (permissions, datetime.now(timezone.utc))
    
    def clear(self, user_id: str) -> None:
        """Clear cached permissions for a specific user."""
        if user_id in self.cache:
            del self.cache[user_id]
    
    def clear_all(self) -> None:
        """Clear all cached permissions."""
        self.cache.clear()
    
    def is_valid(self, user_id: str) -> bool:
        """Check if cached permissions exist and are valid."""
        return self.get(user_id) is not None

permission_cache = PermissionCache()
