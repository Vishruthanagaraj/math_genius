from pathlib import Path

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from . import auth, models, schemas
from .email_utils import send_welcome_email
from .solver import explain_question, get_practice_question, check_practice_answer

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Math Solver Studio")
BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_email(authorization: str | None = Header(default=None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = authorization.split(" ", 1)[1]
    try:
        payload = jwt.decode(token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM])
        email = payload.get("sub")
        if not email:
            raise HTTPException(status_code=401, detail="Invalid token")
        return email
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/register")
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    email = str(user.email).lower()
    existing = db.query(models.User).filter(models.User.email == email).first()
    if existing:
        raise HTTPException(status_code=400, detail="User already exists")
    if not auth.password_is_strong(user.password):
        raise HTTPException(status_code=400, detail=auth.PASSWORD_RULE_TEXT)

    new_user = models.User(
        username=user.username.strip(),
        email=email,
        hashed_password=auth.hash_password(user.password),
    )
    db.add(new_user)
    db.commit()

    sent, status = send_welcome_email(email, user.username.strip())
    return {
        "message": "Registration successful",
        "email": email,
        "username": user.username.strip(),
        "welcome_email_sent": sent,
        "welcome_email_status": status,
    }


@app.post("/login")
def login(user: schemas.UserLogin, db: Session = Depends(get_db)):
    email = str(user.email).lower()
    db_user = db.query(models.User).filter(models.User.email == email).first()
    if not db_user:
        raise HTTPException(status_code=400, detail="User not found")
    if not auth.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect password")

    token = auth.create_access_token({"sub": db_user.email})
    return {
        "message": "Login successful",
        "access_token": token,
        "token_type": "bearer",
        "username": db_user.username,
        "email": db_user.email,
    }


@app.post("/solve")
def solve_math(payload: schemas.SolveRequest, user_email: str = Depends(get_current_email), db: Session = Depends(get_db)):
    question = payload.question.strip()
    if not question:
        raise HTTPException(status_code=422, detail="Question is required")
    steps, answer, beginner_note = explain_question(question)
    item = models.SolveHistory(user_email=user_email, question=question, answer=answer)
    db.add(item)
    db.commit()
    return {"steps": steps, "answer": answer, "beginner_note": beginner_note}


@app.get("/history")
def history(user_email: str = Depends(get_current_email), db: Session = Depends(get_db)):
    rows = (
        db.query(models.SolveHistory)
        .filter(models.SolveHistory.user_email == user_email)
        .order_by(models.SolveHistory.id.desc())
        .all()
    )
    return [{"question": r.question, "answer": r.answer, "created_at": str(r.created_at or "")} for r in rows]


@app.delete("/history")
def clear_history(user_email: str = Depends(get_current_email), db: Session = Depends(get_db)):
    db.query(models.SolveHistory).filter(models.SolveHistory.user_email == user_email).delete()
    db.commit()
    return {"message": "History cleared"}


@app.post("/practice/question")
def practice_question(payload: schemas.PracticeRequest, user_email: str = Depends(get_current_email)):
    try:
        return get_practice_question(payload.topic, payload.difficulty)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/practice/check")
def practice_check(payload: schemas.PracticeAnswerRequest, user_email: str = Depends(get_current_email)):
    return check_practice_answer(payload.topic, payload.question, payload.expected_answer, payload.user_answer)


app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIR)), name="assets")


@app.get("/")
def root():
    return FileResponse(str(FRONTEND_DIR / "index.html"))
