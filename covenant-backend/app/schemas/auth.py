from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str
    role: str
    plan: str
    company_name: str | None = None
    job_title: str | None = None
    phone_number: str | None = None
    created_at: datetime

    class Config:
        from_attributes = True


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class ProfileUpdate(BaseModel):
    full_name: str | None = None
    company_name: str | None = None
    job_title: str | None = None
    phone_number: str | None = None


class PasswordChangeRequest(BaseModel):
    current_password: str
    new_password: str
