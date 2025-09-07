import redis
import json
import logging
from config import Config

logger = logging.getLogger(__name__)

class RedisClient:
    _instance = None
    
    def __init__(self):
        if Config.USE_REDIS:
            try:
                self.redis_client = redis.from_url(Config.REDIS_URL)
                self.redis_client.ping()  # Test connection
                logger.info("Redis connection established successfully")
            except redis.ConnectionError as e:
                logger.warning(f"Redis not available: {e}. Using in-memory mode.")
                self.redis_client = None
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                self.redis_client = None
        else:
            self.redis_client = None
            logger.info("Redis disabled, using in-memory storage")
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def set_user_session(self, user_id, session_data):
        """Store user session data with expiration"""
        if self.redis_client:
            key = f"user_session:{user_id}"
            try:
                self.redis_client.setex(
                    key, 
                    Config.SESSION_TIMEOUT, 
                    json.dumps(session_data)
                )
                return True
            except redis.RedisError as e:
                logger.error(f"Error setting user session: {e}")
                return False
        return True  # Success for in-memory mode (no storage needed)
    
    def get_user_session(self, user_id):
        """Retrieve user session data"""
        if self.redis_client:
            key = f"user_session:{user_id}"
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except (redis.RedisError, json.JSONDecodeError) as e:
                logger.error(f"Error getting user session: {e}")
                return None
        return None
    
    def delete_user_session(self, user_id):
        """Remove user session data"""
        if self.redis_client:
            key = f"user_session:{user_id}"
            try:
                self.redis_client.delete(key)
                return True
            except redis.RedisError as e:
                logger.error(f"Error deleting user session: {e}")
                return False
        return True
    
    def set_request_state(self, puppet_id, backend_message_id, state_data):
        """Store request state for tracking"""
        if self.redis_client:
            key = f"request_state:{puppet_id}:{backend_message_id}"
            try:
                self.redis_client.setex(
                    key,
                    Config.SESSION_TIMEOUT,
                    json.dumps(state_data)
                )
                return True
            except redis.RedisError as e:
                logger.error(f"Error setting request state: {e}")
                return False
        return True
    
    def get_request_state(self, puppet_id, backend_message_id):
        """Retrieve request state"""
        if self.redis_client:
            key = f"request_state:{puppet_id}:{backend_message_id}"
            try:
                data = self.redis_client.get(key)
                return json.loads(data) if data else None
            except (redis.RedisError, json.JSONDecodeError) as e:
                logger.error(f"Error getting request state: {e}")
                return None
        return None
    
    def delete_request_state(self, puppet_id, backend_message_id):
        """Remove request state"""
        if self.redis_client:
            key = f"request_state:{puppet_id}:{backend_message_id}"
            try:
                self.redis_client.delete(key)
                return True
            except redis.RedisError as e:
                logger.error(f"Error deleting request state: {e}")
                return False
        return True

# Global redis client instance
redis_client = RedisClient().get_instance()