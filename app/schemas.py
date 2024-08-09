from datetime import datetime
from typing import Any, Dict, List
from uuid import UUID
from pydantic import BaseModel, Field
from fastapi import Body

class TokenSchema(BaseModel):
    email: str
    name: str
    access_token: str
    refresh_token: str
    
    
class TokenPayload(BaseModel):
    email: str = None
    iat: int = None


class UserAuth(BaseModel):
    email: str = Field(..., description="user email")
    name: str =Field(..., description="user name")
    password: str = Field(..., min_length=5, max_length=24, description="user password")
    

class UserOut(BaseModel):
    _id: str
    email: str
    name: str

class User(UserOut):
    password: str
    
    
class Tool(BaseModel):
    pass


class Assistant(BaseModel):
    id: str
    created_at: int
    description: Any
    file_ids: List
    instructions: str
    metadata: Dict[str, Any]
    model: str
    name: str
    object: str
    tools: List[Tool]
    
class GenerateResponseInput(BaseModel):
    message_body: str
    conv_id: str

class Conversation(BaseModel):
    title: str
    created_at: datetime
    updated_at: datetime
    thread_id: str
    assistant_id: str
    conv_id: UUID
    user_id: str
    status: str
    emailsend: bool = False

class Message(BaseModel):
    text: str
    type: str
class ConvMessages(BaseModel):
    content: List[Message]
    role: str
    created_at: datetime

class ProjectRequirements(BaseModel):
    requirements: str = None
    client_id: str = None
    conv_id:str = None

class InputRequirements(BaseModel):
    prompt: str
    designSystem: str
    styling: str
    numberOfGenerations: int
    shouldAwaitGenerations: str
    
class Developer():
    name: str | None
    email: str | None
    phone: str | None
    location: str | None
    socialUrl: datetime | None
    experience: List[str] | None
    designation: str | None
    languages: List[str] | None
    education: List[str] | None
    yearsOfExperience: int | None
    price: int | None   
    status: str | None
    registerDate: datetime | None

