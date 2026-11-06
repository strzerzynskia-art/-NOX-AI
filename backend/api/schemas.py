from pydantic import BaseModel, Field
from typing import Optional


class CharacterSchema(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    age: Optional[str] = None
    appearance: str = ""
    personality: str = ""
    backstory: str = ""
    scenario: str = ""
    first_message: str = ""


class MessageSchema(BaseModel):
    speaker_name: str
    content: str
    message_type: str = "dialogue"
