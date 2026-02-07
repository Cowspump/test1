from dotenv import load_dotenv
import models, database
from sqlalchemy.orm import Session
import logging

load_dotenv()

from openai import OpenAI

client = OpenAI()
logger = logging.getLogger(__name__)


def generate_user_summary(user_id: int, db: Session) -> dict:
    """
    Генерирует AI-саммари на основе журналов и тестов пользователя.

    Returns:
        dict: {"success": bool, "error": str | None}
    """
    try:
        # Получаем данные
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

        # Валидация: проверяем, что есть хотя бы какие-то данные
        if not journals and not tests:
            logger.info(f"No data available for user {user_id}, skipping summary generation")
            return {"success": False, "error": "No data available"}

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
        {test_text if test_text else "Нет данных"}

        Заметки:
        {journal_text if journal_text else "Нет данных"}

        Сформулируй:
        - общее состояние
        - тенденции
        - краткий совет
        """

        # Правильный вызов OpenAI API
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты психологический ассистент, который анализирует данные пользователя."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=500,
            temperature=0.7
        )

        result = response.choices[0].message.content

        # Валидация результата
        if not result or len(result.strip()) < 10:
            logger.error(f"GPT returned empty or too short response for user {user_id}")
            return {"success": False, "error": "Invalid GPT response"}

        if len(result) > 2000:
            logger.warning(f"GPT response too long for user {user_id}, truncating")
            result = result[:2000]

        # Сохраняем в БД
        summary = models.AISummary(
            user_id=user_id,
            summary_text=result
        )
        db.add(summary)
        db.commit()

        logger.info(f"Successfully generated summary for user {user_id}")
        return {"success": True, "error": None}

    except Exception as e:
        logger.error(f"AI summary error for user {user_id}: {e}", exc_info=True)
        db.rollback()
        return {"success": False, "error": str(e)}
