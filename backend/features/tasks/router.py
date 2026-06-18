from fastapi import APIRouter, Depends
from core.db import get_db
from features.tasks.service import create_task
from features.tasks.schemas import UserTaskCreate, UserTask
from sqlalchemy.orm import Session

# Create router instance
router = APIRouter()

@router.post("/create_task/", response_model=UserTask)
async def user_task_create(task: UserTaskCreate, db: Session = Depends(get_db)):
    return create_task(task, db)

