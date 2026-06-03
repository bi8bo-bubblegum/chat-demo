from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str

class TokenEvent(BaseModel):
    type: str = 'token'
    content: str

class DoneEvent(BaseModel):
    type: str = 'done'
    conversation_id: str

class ErrorEvent(BaseModel):
    type: str = 'error'
    message: str