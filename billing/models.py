from sqlalchemy import Column, ForeignKey, Integer, String, Text, UUID, TIMESTAMP
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(UUID, unique=True)
    email = Column(Text, unique=True)
    role = Column(Text)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(UUID, unique=True)
    title = Column(String, index=True)
    fee = Column(Integer)
    cost = Column(Integer)
    created_at = Column(TIMESTAMP)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    assigner_id = Column(Integer, ForeignKey("users.id"))
    task_id = Column(Integer, ForeignKey("tasks.id"))
    type = Column(String)
    created_at = Column(TIMESTAMP)
