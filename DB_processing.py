import sqlalchemy
import logging
from typing import Optional
from sqlalchemy import make_url, create_engine, text
from sqlAlchemy_metadata_creation import init_tables

# Get logger that uses FastAPI's console output
log_writer = logging.getLogger("uvicorn.error")
log_writer.setLevel(logging.INFO)

async def ensure_database_and_tables(
        app_db_url : str,
        admin_db_url : Optional[str ] = None
):
    log_writer.info("inside ensure_database_and_tables")
    url = make_url(app_db_url)
    database = url.database
    if database is None:
        log_writer.error("app_db_url must include database name")  
        raise ValueError("app_db_url must include database name")
    if admin_db_url:
        try:
            admin_engine = create_engine(admin_db_url, pool_pre_ping=True)
            with admin_engine.connect() as conn:
                conn.execute(text(f"CREATE DATABASE IF NOT EXISTS `{database}`"))
                log_writer.info(f"Database '{database}' ensured to exist") 
            admin_engine.dispose()
        except Exception as ex:
            log_writer.error(f"Error while creating database {ex}")
        finally:
            if(admin_engine):
                admin_engine.dispose()
        sync_db_url = str(app_db_url)
        sync_db_url = sync_db_url.replace("mysql+aiomysql", "mysql+pymysql")
        await init_tables(sync_db_url, log_writer)
    return

async def delete_database_and_tables():
    log_writer.info("inside delete_database_and_tables")
    return
