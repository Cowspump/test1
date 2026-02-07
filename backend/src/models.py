from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, JSON
from sqlalchemy.orm import relationship
from database import Base
import enum
from datetime import datetime

class UserRole(str, enum.Enum):
    worker = "worker"
    therapist = "therapist"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String)
    mail = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(Enum(UserRole), default=UserRole.worker)

    journals = relationship("Journal", back_populates="owner")
    test_results = relationship("TestResult", back_populates="user")

class Journal(Base):
    __tablename__ = "journals"
    id = Column(Integer, primary_key=True, index=True)
    wellbeing_score = Column(Integer)
    note_text = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="journals")

class Question(Base):
    __tablename__ = "questions"
    id = Column(Integer, primary_key=True)
    text = Column(String)
    options = Column(JSON) # [{'text': 'Хорошо', 'points': 5}, ...]

class TestResult(Base):
    __tablename__ = "test_results"
    id = Column(Integer, primary_key=True)
    total_score = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="test_results")

class AILog(Base):
    __tablename__ = "ai_logs"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    request = Column(String)
    response = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)