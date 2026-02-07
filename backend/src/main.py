from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import models, auth, database
import schemas

models.Base.metadata.create_all(bind=database.engine)

app = FastAPI(title="Psychology & AI System")


# --- AUTH ---
@app.post("/token")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = db.query(models.User).filter(models.User.mail == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token = auth.create_access_token(data={"sub": user.mail})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/register")
def register(full_name: str, mail: str, password: str, role: str, db: Session = Depends(database.get_db)):
    try:
        user_role = models.UserRole(role)
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid role. Must be 'worker' or 'therapist'")

    existing_user = db.query(models.User).filter(models.User.mail == mail).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pwd = auth.get_password_hash(password)
    new_user = models.User(full_name=full_name, mail=mail, hashed_password=hashed_pwd, role=user_role)
    db.add(new_user)
    db.commit()
    return {"message": "User created"}


# --- JOURNAL ---
@app.post("/journal")
def log_wellbeing(score: int, note: str = None, user: models.User = Depends(auth.get_current_user),
                  db: Session = Depends(database.get_db)):
    if not (0 <= score <= 5):
        raise HTTPException(status_code=400, detail="Score must be 0-5")
    entry = models.Journal(wellbeing_score=score, note_text=note, user_id=user.id)
    db.add(entry)
    db.commit()
    return {"status": "success"}


# --- TESTING ---
@app.post("/test/add-question")
def add_question(
        q_data: schemas.QuestionCreate,  # Используем схему
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут добавлять вопросы")

    # Превращаем Pydantic-модели в обычные словари для базы данных
    options_json = [opt.model_dump() for opt in q_data.options]

    new_q = models.Question(text=q_data.text, options=options_json)
    db.add(new_q)
    db.commit()
    return {"message": "Вопрос успешно добавлен"}


@app.get("/test/questions", response_model=list[schemas.QuestionOut])
def get_questions(
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.worker:
        raise HTTPException(status_code=403, detail="Only workers can take tests")

    questions = db.query(models.Question).all()
    return questions


@app.delete("/test/question/{question_id}")
def delete_question(
        question_id: int,
        user: models.User = Depends(auth.get_current_user),
        db: Session = Depends(database.get_db)
):
    if user.role != models.UserRole.therapist:
        raise HTTPException(status_code=403, detail="Только терапевты могут удалять вопросы")

    question = db.query(models.Question).filter(models.Question.id == question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Вопрос не найден")

    db.delete(question)
    db.commit()
    return {"message": "Вопрос успешно удалён"}


@app.post("/test/submit")
def submit_test(data: schemas.TestSubmit, user: models.User = Depends(auth.get_current_user), db: Session = Depends(database.get_db)):
    if user.role != models.UserRole.worker:
        raise HTTPException(status_code=403, detail="Only workers can submit tests")

    total_score = 0
    for question_id, option_index in data.answers.items():
        question = db.query(models.Question).filter(models.Question.id == question_id).first()
        if not question:
            raise HTTPException(status_code=400, detail=f"Question {question_id} not found")

        if option_index < 0 or option_index >= len(question.options):
            raise HTTPException(status_code=400, detail=f"Invalid option index for question {question_id}")

        total_score += question.options[option_index]["points"]

    result = models.TestResult(total_score=total_score, user_id=user.id)
    db.add(result)
    db.commit()
    return {"message": "Result saved", "total_score": total_score}


# --- AI ASSISTANT ---
@app.post("/ai/ask")
async def ai_ask(prompt: str, user: models.User = Depends(auth.get_current_user),
                 db: Session = Depends(database.get_db)):
    # ТУТ ТВОЯ ЛОГИКА ВЫЗОВА AI (OpenAI API и т.д.)
    ai_reply = f"Hello {user.full_name}, I am your AI assistant. You said: {prompt}"

    log = models.AILog(user_id=user.id, request=prompt, response=ai_reply)
    db.add(log)
    db.commit()
    return {"response": ai_reply}
