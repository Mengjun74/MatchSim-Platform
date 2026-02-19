from dagster import Definitions, load_assets_from_modules
from src.carms.etl import assets, resources

all_assets = load_assets_from_modules([assets])

defs = Definitions(
    assets=all_assets,
    resources={
        "postgres": resources.PostgresResource(),
    },
)
