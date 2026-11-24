from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    username: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class SolveRequest(BaseModel):
    question: str

class PracticeRequest(BaseModel):
    topic: str
    difficulty: str

class PracticeAnswerRequest(BaseModel):
    topic: str
    difficulty: str
    question: str
    expected_answer: str
    user_answer: str
