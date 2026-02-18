from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

# Base Models
class DisciplineBase(SQLModel):
    name: str = Field(index=True)
    name_fr: Optional[str] = None

class Discipline(DisciplineBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    programs: List["Program"] = Relationship(back_populates="discipline")

class SchoolBase(SQLModel):
    name: str = Field(index=True)
    province: Optional[str] = None

class School(SchoolBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    programs: List["Program"] = Relationship(back_populates="school")

class ProgramBase(SQLModel):
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    discipline_id: Optional[int] = Field(default=None, foreign_key="discipline.id")
    school_id: Optional[int] = Field(default=None, foreign_key="school.id")

class Program(ProgramBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    
    discipline: Optional[Discipline] = Relationship(back_populates="programs")
    school: Optional[School] = Relationship(back_populates="programs")
    sections: List["ProgramSection"] = Relationship(back_populates="program")

class ProgramSectionBase(SQLModel):
    title: str
    content: str
    program_id: Optional[int] = Field(default=None, foreign_key="program.id")

class ProgramSection(ProgramSectionBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    program: Optional[Program] = Relationship(back_populates="sections")

class ETLRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
