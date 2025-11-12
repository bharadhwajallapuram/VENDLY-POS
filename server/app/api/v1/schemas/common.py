from uuid import UUID

from pydantic import BaseModel


class IdOut(BaseModel):
    id: UUID
