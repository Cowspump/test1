from pydantic import BaseModel
from typing import List


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