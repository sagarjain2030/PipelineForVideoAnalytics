from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from typing import Literal, AsyncGenerator
from enum import Enum
from contextlib import asynccontextmanager
from DB_processing import ensure_database_and_tables, delete_database_and_tables
from dotenv import load_dotenv
import os
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine,AsyncSession
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from sqlAlchemy_metadata_creation import Jobs
load_dotenv()


class Job_Type(str,Enum):
    file = "file"
    rtsp = "rtsp"

async_engine = None
AsyncSessionLocal = None

@asynccontextmanager
async def lifespan(app: FastAPI):
     global async_engine, AsyncSessionLocal
     app_db_url = os.getenv("APP_DB_URL")
     admin_db_url = os.getenv("ADMIN_DB_URL")
     db_user = os.getenv("DB_USER")
     db_pass = os.getenv("DB_PASS")
     db_host = os.getenv("DB_HOST")
     db_name = os.getenv("DB_NAME")
     await ensure_database_and_tables(app_db_url,admin_db_url)
     async_engine = create_async_engine(app_db_url)
     if async_engine is None:
          raise ValueError("Not able to create connection for db")
     AsyncSessionLocal = sessionmaker(bind=async_engine, class_=AsyncSession, expire_on_commit=False)
     yield
     await delete_database_and_tables()


list_of_jobs = []
app = FastAPI(lifespan=lifespan)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
     async with AsyncSessionLocal() as session:
          yield session

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

@app.get("/")
async def root():
    return {
        "message" :  "Hello from fastAPI"
    }

app.mount("/static",StaticFiles(directory="UI"),name="static")

@app.get("/ui")
async def return_index_page():
     return FileResponse("UI/index.html")

class JobItem(BaseModel):
     file : str
     job_type : Job_Type

@app.post("/jobs/")
async def post_jobs(jobItem : JobItem, session: AsyncSession = Depends(get_session)):       
        prev_length = len(list_of_jobs)
        list_of_jobs.append((jobItem.file, jobItem.job_type.name))
        try:
            job_insert = Jobs(file_name=jobItem.file, job_type=jobItem.job_type)
            session.add(job_insert)
            await session.commit()
            await session.refresh(job_insert)
        except Exception() as ex:
             await session.rollback()
             return {
                  "message" : f"error while writing into DB {ex}"
             }
        curr_length = len(list_of_jobs)
        if(curr_length - prev_length == 1):
            return {
             "message": "job is added successfully"
            }
        else:
             return {
                  "message": "cannot add job right now"
             }

@app.get("/jobs")
async def get_jobs(session : AsyncSession= Depends(get_session)):
        try:
            result = await session.execute(select(Jobs))
            jobs = result.scalars().all()
            if len(jobs) < 1:
                return {
                    "message" : "no job for running"
                }
            else:
                file_job_type_dict = dict()
                for job in jobs:
                    file_job_type_dict[job.file_name] = job.job_type.name
                return file_job_type_dict
        except Exception as ex:
             return {
                  "message" : f"Error while fetching data from DB {ex}"
             }        

@app.get("/items/{item_id}")
async def get_item_id(item_id : int):
    return {
        "item-id" : item_id
    }