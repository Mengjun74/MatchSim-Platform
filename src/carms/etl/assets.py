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
    """Parse markdown descriptions from JSON"""
    json_path = os.path.join(settings.RAW_DATA_DIR, "1503_markdown_program_descriptions.json")
    
    # Load JSON
    try:
        import json
        # Use utf-8-sig to handle BOM if present, and basic error handling
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            # Read file content first to sanitize if needed, but standard json load usually works
            content = f.read()
            # simple cleanup for common issues if needed, but try direct load first
            data = json.loads(content)
    except Exception as e:
        print(f"Error loading descriptions JSON: {e}")
        return pd.DataFrame()

    rows = []
    for item in data:
        content = item.get("page_content", "")
        metadata = item.get("metadata", {})
        source_url = metadata.get("source", "")
        
        # Extract program_id from URL
        # Example: .../program/1503/27447?programLanguage=en
        # We need the last numeric part before query params
        try:
            # simple parsing: split by '/' and find the one that looks like an ID
            # URL structure seems to be .../program/<match_year>/<program_id>?...
            parts = source_url.split('?')[0].split('/')
            if parts[-1].isdigit():
                prog_id = int(parts[-1])
            elif parts[-2].isdigit():
                 prog_id = int(parts[-2])
            else:
                continue
                
            # Title is often the first line of content
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines else "Program Description"
            
            # Store metadata as JSON string (renamed to extra_data to avoid reserved keyword)
            import json
            meta_json = json.dumps(metadata)
            
            rows.append({
                "program_id": prog_id,
                "title": title,
                "content": content,
                "extra_data": meta_json
            })
        except Exception:
            continue

    return pd.DataFrame(rows)

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
        # We also want to update the 'extra_data' field on the Program table if available.
        
        if not program_descriptions_df.empty:
            # Separating logic:
            # 1. Update Program table with extra_data (if we can match by ID)
            # 2. Insert into ProgramSection
            
            # For 2. ProgramSection
            # We map 'program_id', 'title', 'content' -> ProgramSection
            sections_df = program_descriptions_df[["program_id", "title", "content"]].copy()
            sections_df.to_sql("programsection", conn, if_exists="append", index=False)
            
            # For 1. Metadata update on Program table
            # SQLModel/SQLAlchemy bulk update is tricky with pandas. 
            # Given 'Lite' scope, we can iterate or use a temp table.
            # Let's use a temp table approach for speed.
            meta_df = program_descriptions_df[["program_id", "extra_data"]].dropna()
            if not meta_df.empty:
                meta_df.to_sql("temp_program_meta", conn, if_exists="replace", index=False)
                conn.execute(text("""
                    UPDATE program
                    SET extra_data = temp_program_meta.extra_data
                    FROM temp_program_meta
                    WHERE program.id = temp_program_meta.program_id
                """))
                conn.execute(text("DROP TABLE temp_program_meta"))
            
    return Output(None, metadata={
        "disciplines_count": len(transform_disciplines_asset),
        "schools_count": len(transform_schools_asset),
        "programs_count": len(transform_programs_asset),
        "sections_count": len(program_descriptions_df)
    })
