from typing import Optional, List
from pydantic import BaseModel, Field


class CharacterSchema(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    age: Optional[str] = None
    appearance: str = ""
    personality: str = ""
    backstory: str = ""
    scenario: str = ""
    first_message: str = ""
    avatar: str = ""
    personality_tags: List[str] = Field(default_factory=list)
    secrets: str = ""
    relationships: str = ""
    complex_relationships: bool = True
    evolving_personality: bool = True
    enhanced_memory: bool = True
    theme: str = "cyber"


class MessageSchema(BaseModel):
    character_id: Optional[int] = None
    speaker_name: Optional[str] = Field(default=None, min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=8000)
    message_type: str = "dialogue"


class MemorySchema(BaseModel):
    character_name: str = Field(min_length=1, max_length=80)
    content: str = Field(min_length=1, max_length=3000)
    memory_type: str = "event"
