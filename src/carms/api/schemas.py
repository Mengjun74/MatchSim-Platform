from typing import List, Optional
from pydantic import BaseModel

class DisciplineRead(BaseModel):
    id: int
    name: str

class SchoolRead(BaseModel):
    id: int
    name: str

class ProgramSectionRead(BaseModel):
    id: int
    title: str
    content: str

class ProgramRead(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    discipline_id: Optional[int] = None
    school_id: Optional[int] = None
    # Include names for convenience in API
    discipline_name: Optional[str] = None
    school_name: Optional[str] = None
    extra_data: Optional[str] = None # JSON string

class ProgramDetailRead(ProgramRead):
    sections: List[ProgramSectionRead] = []

class AnalyticsOverview(BaseModel):
    total_programs: int
    total_disciplines: int
    total_schools: int
    avg_sections_per_program: float
