from dataclasses import dataclass, asdict
from typing import Dict, Any
from datetime import datetime

@dataclass
class RequestState:
    """Request state tracking model"""
    user_id: int
    session_id: str
    query: str
    puppet_id: str
    backend_message_id: int
    timestamp: float
    status: str = 'pending'  # pending, processing, completed, failed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'RequestState':
        """Create from dictionary"""
        return cls(**data)
    
    def is_expired(self, timeout_seconds: int = 300) -> bool:
        """Check if request has expired"""
        current_time = datetime.now().timestamp()
        return current_time - self.timestamp > timeout_seconds
    
    def update_status(self, new_status: str):
        """Update request status"""
        valid_statuses = ['pending', 'processing', 'completed', 'failed']
        if new_status in valid_statuses:
            self.status = new_status

class RequestStateManager:
    """Manager for request states"""
    
    @staticmethod
    def create_state(user_id: int, session_id: str, query: str, 
                    puppet_id: str, backend_message_id: int) -> RequestState:
        """Create a new request state"""
        return RequestState(
            user_id=user_id,
            session_id=session_id,
            query=query,
            puppet_id=puppet_id,
            backend_message_id=backend_message_id,
            timestamp=datetime.now().timestamp()
        )
    
    @staticmethod
    def validate_state(state: RequestState) -> bool:
        """Validate state data integrity"""
        if not state or not state.user_id or not state.session_id:
            return False
        
        if not state.puppet_id or not state.backend_message_id:
            return False
        
        if state.timestamp <= 0:
            return False
        
        return True