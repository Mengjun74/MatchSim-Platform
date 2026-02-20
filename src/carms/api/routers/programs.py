from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from sqlmodel import select, func, col
from src.carms.api.deps import SessionDep
from src.carms.db.models import Discipline, School, Program, ProgramSection
from src.carms.api.schemas import (
    DisciplineRead, SchoolRead, ProgramRead, ProgramDetailRead, ProgramSectionRead
)

router = APIRouter()

@router.get("/disciplines", response_model=List[DisciplineRead])
def get_disciplines(session: SessionDep):
    """Retrieve all available medical disciplines."""
    return session.exec(select(Discipline)).all()

@router.get("/schools", response_model=List[SchoolRead])
def get_schools(session: SessionDep):
    """Retrieve all available medical schools."""
    return session.exec(select(School)).all()

@router.get("/programs", response_model=List[ProgramRead])
def get_programs(
    session: SessionDep,
    school_id: Optional[int] = None,
    discipline_id: Optional[int] = None,
    search: Optional[str] = None,
    offset: int = 0,
    limit: int = Query(default=100, le=1000),
):
    """
    Retrieve a paginated list of residency programs.
    Supports filtering by school, discipline, and name-based search.
    """
    # Build query with joins for enriched data (school/discipline names)
    stmt = (
        select(Program, Discipline.name, School.name)
        .join(Discipline, isouter=True)
        .join(School, isouter=True)
    )
    
    # Apply filters
    if school_id:
        stmt = stmt.where(Program.school_id == school_id)
    if discipline_id:
        stmt = stmt.where(Program.discipline_id == discipline_id)
    if search:
        stmt = stmt.where(col(Program.name).contains(search))
        
    results = session.exec(stmt.offset(offset).limit(limit)).all()
    
    response = []
    for prog, disc_name, school_name in results:
        response.append(ProgramRead(
            id=prog.id,
            name=prog.name,
            description=prog.description,
            url=prog.url,
            discipline_id=prog.discipline_id,
            school_id=prog.school_id,
            discipline_name=disc_name,
            school_name=school_name,
            extra_data=prog.extra_data
        ))
        
    return response

@router.get("/programs/{program_id}", response_model=ProgramDetailRead)
def get_program_detail(program_id: int, session: SessionDep):
    """
    Retrieve comprehensive details for a specific residency program,
    including its descriptive markdown sections.
    """
    program = session.get(Program, program_id)
    if not program:
        raise HTTPException(status_code=404, detail="Program not found")
        
    # Fetch related display names
    disc = session.get(Discipline, program.discipline_id) if program.discipline_id else None
    school = session.get(School, program.school_id) if program.school_id else None
    
    # Fetch detail sections
    sections = session.exec(select(ProgramSection).where(ProgramSection.program_id == program_id)).all()
    section_reads = [ProgramSectionRead(id=s.id, title=s.title, content=s.content) for s in sections]
    
    return ProgramDetailRead(
        id=program.id,
        name=program.name,
        description=program.description,
        url=program.url,
        discipline_id=program.discipline_id,
        school_id=program.school_id,
        discipline_name=disc.name if disc else None,
        school_name=school.name if school else None,
        extra_data=program.extra_data,
        sections=section_reads
    )
