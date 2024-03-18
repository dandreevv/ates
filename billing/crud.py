import random
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from . import models
from .kafka import send_costed_task


def get_user_by_id(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def add_task(db: Session, message: dict):
    task = models.Task(
        public_id=message["task_pub_id"],
        title=message["title"],
        fee=random.randint(10, 21),
        cost=random.randint(20, 41),
        created_at=datetime.now(),
    )
    db.add(task)
    db.commit()
    send_costed_task(task)


def get_transactions_summary(db: Session):
    transactions = db.query(models.Transaction).filter(
        models.Transaction.created_at == datetime.now(),
        models.Transaction.type == "fee | costs",
    ).all()
    summary = 0
    for transaction in transactions:
        summary = summary + transaction.fee - transaction.cost
    return summary


def get_transactions_by_assigner(db: Session, user_id: int):
    return db.query(models.Transaction).filter(
        models.Transaction.assigner_id == user_id
    ).all()


def done_billing(db: Session, _: dict):
    developers = db.query(models.User).filter(
        models.User.role == "developer"
    ).all()
    for developer in developers:
        balance = db.query(models.Transaction).filter(
            models.Transaction.assigner_id == developer.id,
            models.Transaction.created_at == (datetime.now() - timedelta(days=1)),
            models.Transaction.type == "payment",
        ).first()
        transactions = db.query(models.Transaction).filter(
            models.Transaction.assigner_id == developer.id,
            models.Transaction.created_at == datetime.now(),
        ).all()
        for transaction in transactions:
            balance = balance + transaction.cost - transaction.fee
        transaction = models.Transaction(
            assigner_id=developer.id,
            task_id=None,
            type="payment",
            created_at=datetime.now(),
        )
        db.add(transaction)
        db.commit()


def add_fee_transaction(db: Session, message: dict):
    transaction = models.Transaction(
        assigner_id=message["assigner_pub_id"],
        task_id=message["task_pub_id"],
        type="fees",
        created_at=datetime.now(),
    )
    db.add(transaction)
    db.commit()


def add_cost_transaction(db: Session, message: dict):
    transaction = models.Transaction(
        assigner_id=message["assigner_pub_id"],
        task_id=message["task_pub_id"],
        type="costs",
        created_at=datetime.now(),
    )
    db.add(transaction)
    db.commit()
