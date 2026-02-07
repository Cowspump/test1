from pydantic import BaseModel
from typing import List
from datetime import datetime

class OptionCreate(BaseModel):
    text: str
    points: int


class QuestionCreate(BaseModel):
    text: str
    options: List[OptionCreate]


class OptionOut(BaseModel):
    text: str
    points: int


class QuestionOut(BaseModel):
    id: int
    text: str
    options: List[OptionOut]

    class Config:
        from_attributes = True




class TestSubmit(BaseModel):
    answers: dict[int, int]  # {question_id: selected_option_index}

class TestResultOut(BaseModel):
    id: int
    total_score: int
    created_at: datetime

    class Config:
        from_attributes = True


class TestResultsResponse(BaseModel):
    message: str
    results: List[TestResultOut]


class QuestionsResponse(BaseModel):
    message: str
    questions: List[QuestionOut]


class JournalOut(BaseModel):
    id: int
    wellbeing_score: int
    note_text: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class JournalsResponse(BaseModel):
    message: str
    journals: List[JournalOut]