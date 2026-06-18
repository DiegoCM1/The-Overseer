from features.tasks.schemas import UserTaskCreate
from features.tasks.models import Tasks
from sqlalchemy.orm import Session

# Create task and insert to DB
def create_task(UserTaskInput: UserTaskCreate, db: Session):
    # Define model
    db_task = Tasks(
        task_name = UserTaskInput.task_name,
        task_source = UserTaskInput.task_source,
        finish_criteria = UserTaskInput.finish_criteria,
        deadline = UserTaskInput.deadline,
        notification_channel = UserTaskInput.notification_channel
    )

    # Initiate db connection
    try:
        db.add(db_task)
        db.commit()
        db.refresh(db_task)
        return db_task
    except ValueError:
        print("Error: Values are not correct")
    finally:
        print("Execution completed")




# 