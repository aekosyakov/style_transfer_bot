"""Redis client for user data and session management."""

import json
import logging
from typing import Optional, Dict, Any
import redis
from config import config

logger = logging.getLogger(__name__)


class RedisClient:
    """Redis client wrapper for bot data storage."""
    
    def __init__(self):
        self.redis = None
        self._connect()
    
    def _connect(self) -> None:
        """Establish Redis connection."""
        try:
            self.redis = redis.from_url(config.redis_url, decode_responses=True)
            # Test connection
            self.redis.ping()
            logger.info("Connected to Redis successfully")
        except redis.RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise
    
    def set_user_premium(self, user_id: int, is_premium: bool = True, duration_days: int = 30) -> bool:
        """Set user premium status."""
        try:
            key = f"user:{user_id}:premium"
            if is_premium:
                # Set with expiration
                self.redis.setex(key, duration_days * 24 * 3600, "true")
            else:
                self.redis.delete(key)
            
            logger.info(f"Set premium status for user {user_id}: {is_premium}")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to set premium status for user {user_id}: {e}")
            return False
    
    def is_user_premium(self, user_id: int) -> bool:
        """Check if user has premium status."""
        try:
            key = f"user:{user_id}:premium"
            return self.redis.exists(key) > 0
        except redis.RedisError as e:
            logger.error(f"Failed to check premium status for user {user_id}: {e}")
            return False
    
    def set_user_data(self, user_id: int, data: Dict[str, Any]) -> bool:
        """Store user data."""
        try:
            key = f"user:{user_id}:data"
            self.redis.hset(key, mapping={k: json.dumps(v) for k, v in data.items()})
            logger.debug(f"Stored user data for {user_id}")
            return True
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Failed to store user data for {user_id}: {e}")
            return False
    
    def get_user_data(self, user_id: int, field: Optional[str] = None) -> Optional[Any]:
        """Retrieve user data."""
        try:
            key = f"user:{user_id}:data"
            
            if field:
                # Get specific field
                value = self.redis.hget(key, field)
                return json.loads(value) if value else None
            else:
                # Get all fields
                data = self.redis.hgetall(key)
                return {k: json.loads(v) for k, v in data.items()} if data else {}
        
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error(f"Failed to retrieve user data for {user_id}: {e}")
            return None
    
    def set_user_language(self, user_id: int, language: str) -> bool:
        """Set user's preferred language."""
        return self.set_user_data(user_id, {"language": language})
    
    def get_user_language(self, user_id: int) -> Optional[str]:
        """Get user's preferred language."""
        return self.get_user_data(user_id, "language")
    
    def increment_usage(self, user_id: int, category: str) -> int:
        """Increment usage counter for a category."""
        try:
            key = f"user:{user_id}:usage:{category}"
            count = self.redis.incr(key)
            # Set expiration for 24 hours if it's a new key
            if count == 1:
                self.redis.expire(key, 24 * 3600)
            return count
        except redis.RedisError as e:
            logger.error(f"Failed to increment usage for user {user_id}, category {category}: {e}")
            return 0
    
    def get_usage_count(self, user_id: int, category: str) -> int:
        """Get usage count for a category."""
        try:
            key = f"user:{user_id}:usage:{category}"
            count = self.redis.get(key)
            return int(count) if count else 0
        except (redis.RedisError, ValueError) as e:
            logger.error(f"Failed to get usage count for user {user_id}, category {category}: {e}")
            return 0
    
    def store_image_request(self, user_id: int, request_id: str, request_data: Dict[str, Any]) -> bool:
        """Store image processing request data."""
        try:
            key = f"request:{request_id}"
            data = {
                "user_id": user_id,
                "timestamp": request_data.get("timestamp"),
                "category": request_data.get("category"),
                "options": json.dumps(request_data.get("options", {})),
                "status": "pending"
            }
            self.redis.hset(key, mapping=data)
            # Set expiration for 1 hour
            self.redis.expire(key, 3600)
            logger.debug(f"Stored image request {request_id} for user {user_id}")
            return True
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error(f"Failed to store image request {request_id}: {e}")
            return False
    
    def get_image_request(self, request_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve image processing request data."""
        try:
            key = f"request:{request_id}"
            data = self.redis.hgetall(key)
            if data:
                # Parse options back to dict
                data["options"] = json.loads(data.get("options", "{}"))
                data["user_id"] = int(data["user_id"])
                return data
            return None
        except (redis.RedisError, json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to retrieve image request {request_id}: {e}")
            return None
    
    def update_request_status(self, request_id: str, status: str, result_url: Optional[str] = None) -> bool:
        """Update request status and result."""
        try:
            key = f"request:{request_id}"
            update_data = {"status": status}
            if result_url:
                update_data["result_url"] = result_url
            
            self.redis.hset(key, mapping=update_data)
            logger.debug(f"Updated request {request_id} status to {status}")
            return True
        except redis.RedisError as e:
            logger.error(f"Failed to update request {request_id} status: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient() 