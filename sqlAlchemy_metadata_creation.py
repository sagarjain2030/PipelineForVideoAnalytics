from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String, Enum as SQLEnum
from enum import Enum
from sqlalchemy import create_engine

class JobType(Enum):
    file = "file"
    rtsp = "rtsp"

Base = declarative_base()

class Jobs(Base):
    __tablename__ = "jobs"
    id = Column(Integer, primary_key=True, autoincrement=True, index=True)
    file_name = Column(String(1024), nullable=False)
    job_type = Column(SQLEnum(JobType), nullable=False)

async def init_tables(app_db_url, log_writer):
    log_writer.info("Creating tables for DB")
    engine = create_engine(app_db_url)
    with engine.begin() as conn:
        Base.metadata.create_all(conn)
    engine.dispose()