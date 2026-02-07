from dotenv import load_dotenv
import models
import database
from fastapi import Depends
from sqlalchemy.orm import Session

load_dotenv()

from openai import OpenAI

client = OpenAI()


def generate_user_summary(user_id: int, db: Session = Depends(database.get_db)):
    journals = (
        db.query(models.Journal)
        .filter(models.Journal.user_id == user_id)
        .order_by(models.Journal.created_at.desc())
        .limit(10)
        .all()
    )

    tests = (
        db.query(models.TestResult)
        .filter(models.TestResult.user_id == user_id)
        .order_by(models.TestResult.created_at.desc())
        .limit(5)
        .all()
    )

    # Формируем текст для AI
    journal_text = "\n".join(
        [f"- {j.created_at.date()}: {j.note_text} (score: {j.wellbeing_score})"
         for j in journals if j.note_text]
    )

    test_text = "\n".join(
        [f"- {t.created_at.date()}: score {t.total_score}"
         for t in tests]
    )

    prompt = f"""
    Ты психологический ассистент.
    Сделай краткую выжимку состояния пользователя.

    Тесты:
    {test_text}

    Заметки:
    {journal_text}

    Сформулируй:
    - общее состояние
    - тенденции
    - краткий совет
    """

    try:
        response = client.responses.create(
            model="gpt-5-nano",
            input=prompt
        )

        result = response.output_text

        summary = models.AISummary(
            user_id=user_id,
            summary_text=result
        )
        db.add(summary)
        db.commit()

    except Exception as e:
        print("AI summary error:", e)
