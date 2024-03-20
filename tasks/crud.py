import random

from sqlalchemy.orm import Session

from . import models


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def add_user(db: Session, data: dict):
    user = db.query(models.User).filter(models.User.public_id == data["public_id"]).first()
    if user is None:
        db_user = models.User(**data)
        db.add(db_user)
    else:
        user.role = data["role"]
    db.commit()


def update_user(db: Session, data: dict):
    db_user = models.User(**data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def get_all_tasks(db: Session):
    return db.query(models.Task).all()


def get_all_open_tasks(db: Session):
    return db.query(models.Task).filter(models.Task.status != "to do").all()


def get_tasks_by_assigner(db: Session, user_id: int):
    return db.query(models.Task).filter(models.Task.assigner_id == user_id).all()


def get_tasks_by_id(db: Session, task_id: int):
    return db.query(models.Task).filter(models.Task.id == task_id).all()


def find_random_developer(db: Session):
    amount = int(db.query(models.User).count())
    offset = random.randint(1, amount + 1)
    return db.query(models.User).filter(models.User.role == "developer").offset(offset).first()


def add_task(db: Session, task):
    db.add(task)
    db.commit()
