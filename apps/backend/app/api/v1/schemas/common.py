from pydantic import BaseModel
from uuid import UUID

class IdOut(BaseModel):
    id: UUID