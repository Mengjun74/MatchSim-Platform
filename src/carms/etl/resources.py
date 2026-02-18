from dagster import ConfigurableResource
from sqlalchemy import create_engine
from src.carms.config import settings

class PostgresResource(ConfigurableResource):
    connection_string: str = settings.DATABASE_URL
    
    def get_engine(self):
        return create_engine(self.connection_string)
