from pydantic import BaseModel

class ChatResponse(BaseModel):
    type: str
    query: str
    response: str
    thread_id: str
    