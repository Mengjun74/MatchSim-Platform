from fastapi import APIRouter
from sqlmodel import select, func
from src.carms.api.deps import SessionDep
from src.carms.db.models import Discipline, School, Program, ProgramSection
from src.carms.api.schemas import AnalyticsOverview

router = APIRouter()

@router.get("/overview", response_model=AnalyticsOverview)
def get_analytics_overview(session: SessionDep):
    total_programs = session.exec(select(func.count(Program.id))).one()
    total_disciplines = session.exec(select(func.count(Discipline.id))).one()
    total_schools = session.exec(select(func.count(School.id))).one()
    
    # Average sections per program (simple approximation)
    total_sections = session.exec(select(func.count(ProgramSection.id))).one()
    avg_sections = total_sections / total_programs if total_programs > 0 else 0
    
    return AnalyticsOverview(
        total_programs=total_programs,
        total_disciplines=total_disciplines,
        total_schools=total_schools,
        avg_sections_per_program=avg_sections
    )

@router.get("/counts/disciplines")
def get_program_counts_by_discipline(session: SessionDep):
    """Return list of {discipline_name: str, count: int}"""
    stmt = (
        select(Discipline.name, func.count(Program.id))
        .join(Program, isouter=True)
        .group_by(Discipline.name)
        .order_by(func.count(Program.id).desc())
    )
    results = session.exec(stmt).all()
    return [{"discipline": r[0], "count": r[1]} for r in results]

@router.get("/counts/schools")
def get_program_counts_by_school(session: SessionDep):
    """Return list of {school_name: str, count: int}"""
    stmt = (
        select(School.name, func.count(Program.id))
        .join(Program, isouter=True)
        .group_by(School.name)
        .order_by(func.count(Program.id).desc())
    )
    results = session.exec(stmt).all()
    return [{"school": r[0], "count": r[1]} for r in results]
