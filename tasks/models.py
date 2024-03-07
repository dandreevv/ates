from sqlalchemy import Column, ForeignKey, Integer, String, Text, UUID, Float, TIMESTAMP
from sqlalchemy.orm import relationship

from .db import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    public_id = Column(UUID, unique=True)
    email = Column(Text, unique=True)
    role = Column(Text)

    tasks = relationship("Task", back_populates="assigner")


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    title = Column(String, index=True)
    assigner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP)

    assigner = relationship("User", back_populates="tasks")
