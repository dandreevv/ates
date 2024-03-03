from sqlalchemy.orm import Session

from . import models


def get_user_by_id(db: Session, id: str):
    return db.query(models.User).filter(models.User.public_id == id).first()


def get_all_tasks(db: Session):
    return db.query(models.Tasks).all()


def get_tasks_by_assigner(db: Session, user_id: str):
    return db.query(models.Tasks).filter(models.Tasks.assigner_id == user_id).all()


def find_random_developer(db: Session):
    amount = int(db.query(models.User).count())
    return db.query(models.User).filter(models.User.role == "developer").offset(amount).first()


def add_task(db: Session, task):
    db.add(task)
    db.commit()


def add_user(db: Session, data: dict):
    db_user = models.User(**data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


def update_user(db: Session, data: dict):
    db_user = models.User(**data)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
