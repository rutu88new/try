from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

@dataclass
class UserSession:
    """User session data model"""
    user_id: int
    original_query: str
    current_index: int = 0
    total_files: int = 0
    buttons_data: List[Dict[str, Any]] = None
    session_id: str = None
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.buttons_data is None:
            self.buttons_data = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = self.created_at
        if self.session_id is None:
            import uuid
            self.session_id = str(uuid.uuid4())[:8]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        data = asdict(self)
        # Convert datetime objects to ISO format strings
        data['created_at'] = self.created_at.isoformat()
        data['last_activity'] = self.last_activity.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'UserSession':
        """Create from dictionary"""
        # Convert string dates back to datetime objects
        if 'created_at' in data and isinstance(data['created_at'], str):
            data['created_at'] = datetime.fromisoformat(data['created_at'])
        if 'last_activity' in data and isinstance(data['last_activity'], str):
            data['last_activity'] = datetime.fromisoformat(data['last_activity'])
        
        return cls(**data)
    
    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.now()
    
    def is_expired(self, timeout_minutes: int = 5) -> bool:
        """Check if session has expired"""
        return datetime.now() - self.last_activity > timedelta(minutes=timeout_minutes)
    
    def get_next_button_data(self) -> Optional[Dict[str, Any]]:
        """Get next button data if available"""
        if self.current_index < len(self.buttons_data):
            return self.buttons_data[self.current_index]
        return None
    
    def move_to_next(self) -> bool:
        """Move to next file index"""
        if self.current_index + 1 < self.total_files:
            self.current_index += 1
            self.update_activity()
            return True
        return False

class SessionManager:
    """Manager for user sessions"""
    
    @staticmethod
    def create_session(user_id: int, query: str) -> UserSession:
        """Create a new user session"""
        return UserSession(user_id=user_id, original_query=query)
    
    @staticmethod
    def validate_session(session: UserSession) -> bool:
        """Validate session data integrity"""
        if not session or not session.user_id or not session.original_query:
            return False
        
        if session.current_index < 0 or session.total_files < 0:
            return False
        
        if session.current_index >= session.total_files > 0:
            return False
        
        return True