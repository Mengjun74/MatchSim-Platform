from dagster import asset, Output, MetadataValue
import pandas as pd
import os
import zipfile
import io
from sqlalchemy import text
from src.carms.config import settings
from src.carms.db.models import Discipline, School, Program, ProgramSection
from src.carms.db.engine import engine

# ... (Previous assets: raw_disciplines_df, raw_programs_df, transform_disciplines, transform_schools, transform_programs) ...
# Re-declaring for completeness in this file context, usually I'd append but replace is safer here to ensure integrity.

@asset
def raw_disciplines_df() -> pd.DataFrame:
    """Load raw disciplines from Excel"""
    file_path = os.path.join(settings.RAW_DATA_DIR, "1503_discipline.xlsx")
    return pd.read_excel(file_path)

@asset
def raw_programs_df() -> pd.DataFrame:
    """Load raw program master list from Excel"""
    file_path = os.path.join(settings.RAW_DATA_DIR, "1503_program_master.xlsx")
    return pd.read_excel(file_path)

@asset
def transform_disciplines_asset(raw_disciplines_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize disciplines"""
    df = raw_disciplines_df.copy()
    df = df.rename(columns={"discipline": "name"})
    return df[["discipline_id", "name"]]

@asset
def transform_schools_asset(raw_programs_df: pd.DataFrame) -> pd.DataFrame:
    """Extract and clean unique schools from program list"""
    df = raw_programs_df[['school_id', 'school_name']].drop_duplicates().copy()
    df = df.rename(columns={"school_id": "id", "school_name": "name"})
    return df

@asset
def transform_programs_asset(raw_programs_df: pd.DataFrame) -> pd.DataFrame:
    """Clean and standardize programs"""
    df = raw_programs_df.copy()
    # Map columns. We know 'program_stream_id' is the unique ID for a program stream
    df = df.rename(columns={
        "program_stream_id": "id", 
        "program_name": "name", 
        "program_url": "url"
    })
    # Ensure all required columns exist
    for col in ["id", "school_id", "discipline_id", "name", "url"]:
        if col not in df.columns:
            df[col] = None
            
    return df[["id", "school_id", "discipline_id", "name", "url"]]

@asset
def program_descriptions_df() -> pd.DataFrame:
    """Parse markdown descriptions from zip"""
    zip_path = os.path.join(settings.RAW_DATA_DIR, "1503_markdown_program_descriptions.zip")
    data = []
    
    with zipfile.ZipFile(zip_path, 'r') as z:
        for filename in z.namelist():
            if filename.endswith(".md"):
                # Expecting filename format or content to link to program
                # For now, let's assume we can map it via some ID in the filename or just store it.
                # Actually, standard CaRMS structure usually has 'program_id' in filename.
                # Example: "1234.md" -> program_id=1234
                try:
                    prog_id = int(os.path.splitext(os.path.basename(filename))[0])
                    content = z.read(filename).decode('utf-8')
                    # Simple parsing: Title is first line, rest is content
                    lines = content.split('\n')
                    title = lines[0].replace('#', '').strip()
                    body = '\n'.join(lines[1:]).strip()
                    data.append({"program_id": prog_id, "title": title, "content": body})
                except ValueError:
                    continue # Skip files that don't match expected ID format

    return pd.DataFrame(data)

@asset
def load_to_postgres(
    transform_disciplines_asset: pd.DataFrame,
    transform_schools_asset: pd.DataFrame,
    transform_programs_asset: pd.DataFrame,
    program_descriptions_df: pd.DataFrame
):
    """Load all transformed dataframes to Postgres"""
    
    # Ensure tables exist (in case API hasn't started yet)
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    with engine.begin() as conn:
        # Disable FK checks temporarily if needed, or stick to order
        # Postgres doesn't easily allow disabling FKs globally, so delete in reverse order
        conn.execute(text("TRUNCATE TABLE programsection, program, school, discipline RESTART IDENTITY CASCADE"))
        
        transform_disciplines_asset.rename(columns={"discipline_id": "id"}).to_sql(
            "discipline", conn, if_exists="append", index=False
        )
        
        transform_schools_asset.to_sql(
            "school", conn, if_exists="append", index=False
        )
        
        transform_programs_asset.to_sql(
            "program", conn, if_exists="append", index=False
        )
        
        # Load sections (descriptions)
        # We need to map description to program. In our model, we have 'description' field on Program
        # AND 'ProgramSection' table. The markdown is likely sections.
        # For simplicity, let's just insert into ProgramSection
        if not program_descriptions_df.empty:
            program_descriptions_df.to_sql(
                "programsection", conn, if_exists="append", index=False
            )
            
    return Output(None, metadata={
        "disciplines_count": len(transform_disciplines_asset),
        "schools_count": len(transform_schools_asset),
        "programs_count": len(transform_programs_asset),
        "sections_count": len(program_descriptions_df)
    })
