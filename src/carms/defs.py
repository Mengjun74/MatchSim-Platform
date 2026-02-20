"""
Dagster definitions for the CaRMS Platform.
Wires together assets and resources for orchestration.
"""
from dagster import Definitions, load_assets_from_modules
from src.carms.etl import assets, resources

# Automatically discover and load all assets from the assets module
all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "postgres": resources.PostgresResource(),
    },
)
