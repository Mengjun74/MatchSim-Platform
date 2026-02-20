"""
Database models for the CaRMS Platform.
Uses SQLModel to define both the schema and the application-level models.
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship

class DisciplineBase(SQLModel):
    """Base fields for medical disciplines."""
    name: str = Field(index=True)
    name_fr: Optional[str] = None

class Discipline(DisciplineBase, table=True):
    """Database table for medical disciplines."""
    id: Optional[int] = Field(default=None, primary_key=True)
    programs: List["Program"] = Relationship(back_populates="discipline")

class SchoolBase(SQLModel):
    """Base fields for medical schools."""
    name: str = Field(index=True)
    province: Optional[str] = None

class School(SchoolBase, table=True):
    """Database table for medical schools."""
    id: Optional[int] = Field(default=None, primary_key=True)
    programs: List["Program"] = Relationship(back_populates="school")

class ProgramBase(SQLModel):
    """Base fields for residency programs."""
    name: str
    description: Optional[str] = None
    url: Optional[str] = None
    discipline_id: Optional[int] = Field(default=None, foreign_key="discipline.id")
    school_id: Optional[int] = Field(default=None, foreign_key="school.id")
    extra_data: Optional[str] = Field(default=None, description="JSON string containing extended program metadata")

class Program(ProgramBase, table=True):
    """Database table for residency programs."""
    id: Optional[int] = Field(default=None, primary_key=True)
    
    discipline: Optional[Discipline] = Relationship(back_populates="programs")
    school: Optional[School] = Relationship(back_populates="programs")
    sections: List["ProgramSection"] = Relationship(back_populates="program")

class ProgramSectionBase(SQLModel):
    """Base fields for program-specific detail sections."""
    title: str
    content: str
    program_id: Optional[int] = Field(default=None, foreign_key="program.id")

class ProgramSection(ProgramSectionBase, table=True):
    """Database table for program-specific detail sections (e.g., Markdown content)."""
    id: Optional[int] = Field(default=None, primary_key=True)
    program: Optional[Program] = Relationship(back_populates="sections")

class ETLRun(SQLModel, table=True):
    """Tracks the status and history of ETL operations."""
    id: Optional[int] = Field(default=None, primary_key=True)
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
