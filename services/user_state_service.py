from typing import Dict, Optional
from enum import Enum


class UserState(Enum):
    """User states."""
    IDLE = "idle"
    WAITING_FOR_RECIPE_INGREDIENTS = "waiting_for_recipe_ingredients"
    WAITING_FOR_NOTE_CONTENT = "waiting_for_note_content"
    WAITING_FOR_SLIP_ANALYSIS = "waiting_for_slip_analysis"


class UserStateService:
    """Service for managing user states."""
    
    def __init__(self):
        self._user_states: Dict[int, UserState] = {}
    
    def set_user_state(self, user_id: int, state: UserState):
        """Set user state."""
        self._user_states[user_id] = state
    
    def get_user_state(self, user_id: int) -> UserState:
        """Get user state."""
        return self._user_states.get(user_id, UserState.IDLE)
    
    def clear_user_state(self, user_id: int):
        """Clear user state."""
        if user_id in self._user_states:
            del self._user_states[user_id]
    
    def is_waiting_for_recipe(self, user_id: int) -> bool:
        """Check if user is waiting for recipe ingredients."""
        return self.get_user_state(user_id) == UserState.WAITING_FOR_RECIPE_INGREDIENTS
    
    def is_waiting_for_note(self, user_id: int) -> bool:
        """Check if user is waiting for note content."""
        return self.get_user_state(user_id) == UserState.WAITING_FOR_NOTE_CONTENT
    
    def is_waiting_for_slip_analysis(self, user_id: int) -> bool:
        """Check if user is waiting for slip analysis."""
        return self.get_user_state(user_id) == UserState.WAITING_FOR_SLIP_ANALYSIS 