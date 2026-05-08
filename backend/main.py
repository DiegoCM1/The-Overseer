from fastapi import FastAPI
from contextlib import asynccontextmanager
from core.config import settings
from core.db import Base, SessionLocal, engine
from features.tasks.models import Tasks

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🟢 Initializing resources...")
    
    Base.metadata.create_all(engine)
    print("Created all tables in db")

    yield
    # SHUTDOWN
    print("🔴 Shutting down...")


app = FastAPI(lifespan=lifespan)

@app.get("/")
def read_root():
    return {"Hello": "World"}


def get_db():
    db = SessionLocal()
    try: 
        yield db
    finally:
        db.close()

