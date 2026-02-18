from typing import Annotated
from fastapi import Depends
from sqlmodel import Session
from src.carms.db.engine import get_session

# Re-export for convenience
SessionDep = Annotated[Session, Depends(get_session)]
