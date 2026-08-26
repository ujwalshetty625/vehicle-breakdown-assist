from pydantic import BaseModel

class ReplanRequest(BaseModel):
    assignment_id: int