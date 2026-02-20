"""
Dagster assets for ETL processing of CaRMS data.
Handles extraction from Excel/JSON, transformation, and loading into PostgreSQL.
"""
from dagster import asset, Output, MetadataValue
import pandas as pd
import os
import zipfile
import io
import json
from sqlalchemy import text
from src.carms.config import settings
from src.carms.db.models import Discipline, School, Program, ProgramSection
from src.carms.db.engine import engine

@asset
def raw_disciplines_df() -> pd.DataFrame:
    """
    Extracts raw discipline data from the 1503_discipline.xlsx file.
    """
    file_path = os.path.join(settings.RAW_DATA_DIR, "1503_discipline.xlsx")
    return pd.read_excel(file_path)

@asset
def raw_programs_df() -> pd.DataFrame:
    """
    Extracts raw program master data from the 1503_program_master.xlsx file.
    """
    file_path = os.path.join(settings.RAW_DATA_DIR, "1503_program_master.xlsx")
    return pd.read_excel(file_path)

@asset
def transform_disciplines_asset(raw_disciplines_df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardizes discipline names and ensures schema alignment.
    """
    df = raw_disciplines_df.copy()
    df = df.rename(columns={"discipline": "name"})
    return df[["discipline_id", "name"]]

@asset
def transform_schools_asset(raw_programs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extracts unique school entities from the raw program list.
    """
    df = raw_programs_df[['school_id', 'school_name']].drop_duplicates().copy()
    df = df.rename(columns={"school_id": "id", "school_name": "name"})
    return df

@asset
def transform_programs_asset(raw_programs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans and standardizes program information, mapping columns to the target schema.
    """
    df = raw_programs_df.copy()
    # Map raw columns to standardized DB schema names
    df = df.rename(columns={
        "program_stream_id": "id", 
        "program_name": "name", 
        "program_url": "url"
    })
    
    # Ensure all required columns exist for the database model
    for col in ["id", "school_id", "discipline_id", "name", "url"]:
        if col not in df.columns:
            df[col] = None
            
    return df[["id", "school_id", "discipline_id", "name", "url"]]

@asset
def program_descriptions_df() -> pd.DataFrame:
    """
    Parses markdown descriptions and metadata from the source JSON file.
    Extracts IDs and titles from embedded content and URLs.
    """
    json_path = os.path.join(settings.RAW_DATA_DIR, "1503_markdown_program_descriptions.json")
    
    try:
        with open(json_path, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error loading descriptions JSON: {e}")
        return pd.DataFrame()

    rows = []
    for item in data:
        content = item.get("page_content", "")
        metadata = item.get("metadata", {})
        source_url = metadata.get("source", "")
        
        # Parse program_id from the source URL structure
        try:
            parts = source_url.split('?')[0].split('/')
            if parts[-1].isdigit():
                prog_id = int(parts[-1])
            elif parts[-2].isdigit():
                 prog_id = int(parts[-2])
            else:
                continue
                
            # Extract title from the first line of markdown content
            lines = content.split('\n')
            title = lines[0].replace('#', '').strip() if lines else "Program Description"
            
            rows.append({
                "program_id": prog_id,
                "title": title,
                "content": content,
                "extra_data": json.dumps(metadata)
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
    """
    Orchestrates the loading of all transformed assets into PostgreSQL.
    Ensures referential integrity by clearing and loading in order.
    """
    from sqlmodel import SQLModel
    SQLModel.metadata.create_all(engine)

    with engine.begin() as conn:
        # Clear existing data using CASCADE to handle foreign key dependencies
        conn.execute(text("TRUNCATE TABLE programsection, program, school, discipline RESTART IDENTITY CASCADE"))
        
        # Load core lookup tables first
        transform_disciplines_asset.rename(columns={"discipline_id": "id"}).to_sql(
            "discipline", conn, if_exists="append", index=False
        )
        
        transform_schools_asset.to_sql(
            "school", conn, if_exists="append", index=False
        )
        
        # Load main entities
        transform_programs_asset.to_sql(
            "program", conn, if_exists="append", index=False
        )
        
        # Load optional detail sections and update metadata
        if not program_descriptions_df.empty:
            # Insert into ProgramSection table
            sections_df = program_descriptions_df[["program_id", "title", "content"]].copy()
            sections_df.to_sql("programsection", conn, if_exists="append", index=False)
            
            # Update additional metadata on the Program table from the JSON payload
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
